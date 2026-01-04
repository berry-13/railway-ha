"""Railway GraphQL API client."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

from .const import RAILWAY_API_ENDPOINT

# Request timeout for API calls
REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=30)

_LOGGER = logging.getLogger(__name__)


class RailwayApiError(Exception):
    """Base exception for Railway API errors."""


class RailwayAuthError(RailwayApiError):
    """Authentication error."""


class RailwayConnectionError(RailwayApiError):
    """Connection error."""


# GraphQL Queries - Updated based on actual Railway API schema
QUERY_ME = """
query me {
  me {
    id
    name
    email
    avatar
    isVerified
    registrationStatus
  }
}
"""

QUERY_ME_WITH_WORKSPACES = """
query meWithWorkspaces {
  me {
    id
    name
    email
    workspaces {
      id
      name
      customer {
        id
        creditBalance
        currentUsage
        appliedCredits
        remainingUsageCreditBalance
        billingEmail
        state
        isTrialing
        isPrepaying
        trialDaysRemaining
      }
    }
  }
}
"""

QUERY_PROJECTS = """
query projects {
  projects {
    edges {
      node {
        id
        name
        description
        createdAt
        updatedAt
        environments {
          edges {
            node {
              id
              name
            }
          }
        }
        services {
          edges {
            node {
              id
              name
            }
          }
        }
      }
    }
  }
}
"""

QUERY_DEPLOYMENTS = """
query deployments($projectId: String!) {
  project(id: $projectId) {
    services {
      edges {
        node {
          id
          name
          deployments(first: 1) {
            edges {
              node {
                id
                status
                createdAt
              }
            }
          }
        }
      }
    }
  }
}
"""

QUERY_REFERRAL_INFO = """
query referralInfo($workspaceId: String!) {
  referralInfo(workspaceId: $workspaceId) {
    code
    id
    status
    referralStats {
      credited
      pending
    }
  }
}
"""

QUERY_WORKSPACE_TEMPLATES = """
query workspaceTemplates($workspaceId: String!) {
  workspaceTemplates(workspaceId: $workspaceId, first: 50) {
    edges {
      node {
        id
        name
        code
        totalPayout
      }
    }
  }
}
"""

QUERY_TEMPLATE_METRICS = """
query templateMetrics($id: String!) {
  templateMetrics(id: $id) {
    activeDeployments
    deploymentsLast90Days
    earningsLast30Days
    earningsLast90Days
    eligibleForSupportBonus
    supportHealth
    templateHealth
    totalDeployments
    totalEarnings
  }
}
"""


class RailwayApiClient:
    """Railway GraphQL API client."""

    def __init__(
        self,
        api_token: str,
        session: aiohttp.ClientSession,
        token_type: str = "personal",
    ) -> None:
        """Initialize the API client.

        Args:
            api_token: The Railway API token.
            session: The aiohttp client session.
            token_type: Type of token - "personal" or "team".
        """
        self._api_token = api_token.strip()
        self._session = session
        self._token_type = token_type

    def _get_headers(self) -> dict[str, str]:
        """Get the appropriate headers based on token type."""
        headers = {"Content-Type": "application/json"}

        if self._token_type == "team":
            headers["Team-Access-Token"] = self._api_token
        else:
            # Personal/account token uses Bearer auth
            headers["Authorization"] = f"Bearer {self._api_token}"

        return headers

    async def _execute_query(
        self, query: str, variables: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Execute a GraphQL query."""
        headers = self._get_headers()

        payload: dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables

        _LOGGER.debug("Executing query to %s", RAILWAY_API_ENDPOINT)

        try:
            async with self._session.post(
                RAILWAY_API_ENDPOINT,
                headers=headers,
                json=payload,
                timeout=REQUEST_TIMEOUT,
            ) as response:
                response_text = await response.text()
                _LOGGER.debug("Response status: %s", response.status)

                if response.status == 401:
                    _LOGGER.error("Authentication failed (401): %s", response_text)
                    raise RailwayAuthError("Invalid API token")
                if response.status == 403:
                    _LOGGER.error("Access denied (403): %s", response_text)
                    raise RailwayAuthError("Access denied")
                if response.status != 200:
                    truncated_response = response_text[:500] if len(response_text) > 500 else response_text
                    _LOGGER.error(
                        "API request failed with status %s: %s",
                        response.status,
                        truncated_response,
                    )
                    raise RailwayApiError(
                        f"API request failed with status {response.status}: {truncated_response}"
                    )

                try:
                    data = await response.json()
                except (ValueError, aiohttp.ContentTypeError) as err:
                    _LOGGER.error("Failed to parse JSON response: %s", response_text[:500])
                    raise RailwayApiError(f"Invalid JSON response: {err}") from err

                if "errors" in data:
                    errors = data["errors"]
                    error_messages = [e.get("message", str(e)) for e in errors]
                    error_str = "; ".join(error_messages)
                    _LOGGER.error("GraphQL errors: %s", error_str)

                    if any(
                        "auth" in msg.lower()
                        or "unauthorized" in msg.lower()
                        or "not authenticated" in msg.lower()
                        for msg in error_messages
                    ):
                        raise RailwayAuthError(error_str)

                    raise RailwayApiError(f"GraphQL errors: {error_str}")

                return data.get("data", {})

        except aiohttp.ClientError as err:
            _LOGGER.error("Connection error: %s", err)
            raise RailwayConnectionError(f"Connection error: {err}") from err

    async def async_get_me(self) -> dict[str, Any]:
        """Get current user information."""
        data = await self._execute_query(QUERY_ME)
        return data.get("me", {})

    async def async_get_me_with_workspaces(self) -> dict[str, Any]:
        """Get current user information with workspaces and billing."""
        data = await self._execute_query(QUERY_ME_WITH_WORKSPACES)
        return data.get("me", {})

    async def async_get_projects(self) -> list[dict[str, Any]]:
        """Get all projects."""
        data = await self._execute_query(QUERY_PROJECTS)
        projects = data.get("projects", {}).get("edges", [])
        return [edge["node"] for edge in projects]

    async def async_get_deployments(self, project_id: str) -> list[dict[str, Any]]:
        """Get deployments for a project."""
        data = await self._execute_query(QUERY_DEPLOYMENTS, {"projectId": project_id})
        project = data.get("project", {})
        services = project.get("services", {}).get("edges", [])

        deployments = []
        for service_edge in services:
            service = service_edge["node"]
            deployment_edges = service.get("deployments", {}).get("edges", [])
            for dep_edge in deployment_edges:
                deployment = dep_edge["node"]
                deployment["service_name"] = service["name"]
                deployment["service_id"] = service["id"]
                deployments.append(deployment)

        return deployments

    async def async_validate_token(self) -> bool:
        """Validate the API token by fetching user info."""
        try:
            me = await self.async_get_me()
            return bool(me.get("id"))
        except RailwayApiError:
            return False

    async def async_get_referral_info(self, workspace_id: str) -> dict[str, Any]:
        """Get referral info for a workspace."""
        data = await self._execute_query(
            QUERY_REFERRAL_INFO, {"workspaceId": workspace_id}
        )
        return data.get("referralInfo", {})

    async def async_get_workspace_templates(
        self, workspace_id: str
    ) -> list[dict[str, Any]]:
        """Get templates for a workspace."""
        data = await self._execute_query(
            QUERY_WORKSPACE_TEMPLATES, {"workspaceId": workspace_id}
        )
        edges = data.get("workspaceTemplates", {}).get("edges", [])
        return [edge["node"] for edge in edges]

    async def async_get_template_metrics(self, template_id: str) -> dict[str, Any]:
        """Get metrics for a template."""
        data = await self._execute_query(
            QUERY_TEMPLATE_METRICS, {"id": template_id}
        )
        return data.get("templateMetrics", {})

    async def async_get_all_data(self) -> dict[str, Any]:
        """Fetch all data in a single coordinated call."""
        result: dict[str, Any] = {
            "me": {},
            "workspaces": [],
            "projects": [],
            "deployments": {},
            "referrals": {},
            "templates": [],
            "template_metrics": {},
            "earnings": {
                "templates_30d": 0.0,
                "templates_total": 0.0,
                "templates_payout": 0.0,
                "referrals_credited": 0,
                "referrals_pending": 0,
            },
        }

        # Fetch user info with workspaces (includes billing)
        try:
            me_data = await self.async_get_me_with_workspaces()
            result["me"] = {
                "id": me_data.get("id"),
                "name": me_data.get("name"),
                "email": me_data.get("email"),
            }
            result["workspaces"] = me_data.get("workspaces", [])
        except RailwayApiError as err:
            _LOGGER.warning("Failed to fetch user info with workspaces: %s", err)
            # Fallback to basic user info
            try:
                result["me"] = await self.async_get_me()
            except RailwayApiError as err2:
                _LOGGER.warning("Failed to fetch basic user info: %s", err2)

        # Fetch projects
        try:
            result["projects"] = await self.async_get_projects()
        except RailwayApiError as err:
            _LOGGER.warning("Failed to fetch projects: %s", err)

        # Fetch per-project deployments
        for project in result["projects"]:
            project_id = project.get("id")
            if not project_id:
                continue

            try:
                result["deployments"][project_id] = await self.async_get_deployments(
                    project_id
                )
            except RailwayApiError as err:
                _LOGGER.debug(
                    "Failed to fetch deployments for project %s: %s", project_id, err
                )

        # Fetch earnings data per workspace
        total_referrals_credited = 0
        total_referrals_pending = 0
        total_templates_30d = 0.0
        total_templates_total = 0.0
        total_templates_payout = 0.0

        for workspace in result["workspaces"]:
            ws_id = workspace.get("id")
            if not ws_id:
                continue

            # Fetch referral info
            try:
                referral_info = await self.async_get_referral_info(ws_id)
                result["referrals"][ws_id] = referral_info
                stats = referral_info.get("referralStats", {})
                total_referrals_credited += stats.get("credited", 0)
                total_referrals_pending += stats.get("pending", 0)
            except RailwayApiError as err:
                _LOGGER.debug(
                    "Failed to fetch referral info for workspace %s: %s", ws_id, err
                )

            # Fetch templates and their metrics
            try:
                templates = await self.async_get_workspace_templates(ws_id)
                for template in templates:
                    template["workspace_id"] = ws_id
                    result["templates"].append(template)
                    total_templates_payout += template.get("totalPayout", 0) or 0

                    # Fetch metrics for each template
                    template_id = template.get("id")
                    if template_id:
                        try:
                            metrics = await self.async_get_template_metrics(template_id)
                            result["template_metrics"][template_id] = metrics
                            total_templates_30d += metrics.get("earningsLast30Days", 0) or 0
                            total_templates_total += metrics.get("totalEarnings", 0) or 0
                        except RailwayApiError as err:
                            _LOGGER.debug(
                                "Failed to fetch metrics for template %s: %s",
                                template_id,
                                err,
                            )
            except RailwayApiError as err:
                _LOGGER.debug(
                    "Failed to fetch templates for workspace %s: %s", ws_id, err
                )

        # Calculate aggregated earnings
        result["earnings"] = {
            "templates_30d": total_templates_30d,
            "templates_total": total_templates_total,
            "templates_payout": total_templates_payout,
            "referrals_credited": total_referrals_credited,
            "referrals_pending": total_referrals_pending,
        }

        return result
