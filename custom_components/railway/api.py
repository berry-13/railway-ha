"""Railway GraphQL API client."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

from .const import RAILWAY_API_ENDPOINT

_LOGGER = logging.getLogger(__name__)


class RailwayApiError(Exception):
    """Base exception for Railway API errors."""


class RailwayAuthError(RailwayApiError):
    """Authentication error."""


class RailwayConnectionError(RailwayApiError):
    """Connection error."""


# GraphQL Queries
QUERY_ME = """
query me {
  me {
    id
    name
    email
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

QUERY_PROJECT_USAGE = """
query projectUsage($projectId: String!) {
  project(id: $projectId) {
    id
    name
    usage {
      currentUsage
      estimatedUsage
    }
  }
}
"""

QUERY_TEAMS = """
query teams {
  teams {
    edges {
      node {
        id
        name
        avatar
      }
    }
  }
}
"""

QUERY_CUSTOMER = """
query customer {
  customer {
    id
    creditBalance
    billingEmail
    state
  }
}
"""

QUERY_USAGE = """
query usage {
  usage {
    currentUsage
    estimatedUsage
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
                    _LOGGER.error(
                        "API request failed with status %s: %s",
                        response.status,
                        response_text,
                    )
                    raise RailwayApiError(
                        f"API request failed with status {response.status}: {response_text}"
                    )

                try:
                    data = await response.json()
                except Exception as err:
                    _LOGGER.error("Failed to parse JSON response: %s", response_text)
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

    async def async_get_projects(self) -> list[dict[str, Any]]:
        """Get all projects."""
        data = await self._execute_query(QUERY_PROJECTS)
        projects = data.get("projects", {}).get("edges", [])
        return [edge["node"] for edge in projects]

    async def async_get_teams(self) -> list[dict[str, Any]]:
        """Get all teams."""
        data = await self._execute_query(QUERY_TEAMS)
        teams = data.get("teams", {}).get("edges", [])
        return [edge["node"] for edge in teams]

    async def async_get_customer(self) -> dict[str, Any]:
        """Get customer billing information."""
        data = await self._execute_query(QUERY_CUSTOMER)
        return data.get("customer", {})

    async def async_get_usage(self) -> dict[str, Any]:
        """Get usage information."""
        data = await self._execute_query(QUERY_USAGE)
        return data.get("usage", {})

    async def async_get_project_usage(self, project_id: str) -> dict[str, Any]:
        """Get usage for a specific project."""
        data = await self._execute_query(
            QUERY_PROJECT_USAGE, {"projectId": project_id}
        )
        return data.get("project", {})

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

    async def async_get_all_data(self) -> dict[str, Any]:
        """Fetch all data in a single coordinated call."""
        result: dict[str, Any] = {
            "me": {},
            "customer": {},
            "usage": {},
            "projects": [],
            "teams": [],
            "project_usage": {},
            "deployments": {},
        }

        # Fetch user info
        try:
            result["me"] = await self.async_get_me()
        except RailwayApiError as err:
            _LOGGER.warning("Failed to fetch user info: %s", err)

        # Fetch customer/billing info
        try:
            result["customer"] = await self.async_get_customer()
        except RailwayApiError as err:
            _LOGGER.debug("Failed to fetch customer info: %s", err)

        # Fetch usage info
        try:
            result["usage"] = await self.async_get_usage()
        except RailwayApiError as err:
            _LOGGER.debug("Failed to fetch usage info: %s", err)

        # Fetch teams
        try:
            result["teams"] = await self.async_get_teams()
        except RailwayApiError as err:
            _LOGGER.debug("Failed to fetch teams: %s", err)

        # Fetch projects
        try:
            result["projects"] = await self.async_get_projects()
        except RailwayApiError as err:
            _LOGGER.warning("Failed to fetch projects: %s", err)

        # Fetch per-project data
        for project in result["projects"]:
            project_id = project.get("id")
            if not project_id:
                continue

            # Project usage
            try:
                usage = await self.async_get_project_usage(project_id)
                result["project_usage"][project_id] = usage.get("usage", {})
            except RailwayApiError as err:
                _LOGGER.debug("Failed to fetch usage for project %s: %s", project_id, err)

            # Deployments
            try:
                result["deployments"][project_id] = await self.async_get_deployments(
                    project_id
                )
            except RailwayApiError as err:
                _LOGGER.debug(
                    "Failed to fetch deployments for project %s: %s", project_id, err
                )

        return result
