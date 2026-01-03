"""Tests for Railway API client."""

import sys
from pathlib import Path

import aiohttp
import pytest

# Add the railway module directly to path
sys.path.insert(0, str(Path(__file__).parent.parent / "custom_components" / "railway"))

from api import (
    RailwayApiClient,
    RailwayApiError,
    RailwayAuthError,
)


@pytest.mark.asyncio
async def test_get_me(api_token: str, token_type: str) -> None:
    """Test fetching user information."""
    async with aiohttp.ClientSession() as session:
        client = RailwayApiClient(api_token, session, token_type)
        me = await client.async_get_me()

        assert me is not None
        assert "id" in me
        assert me["id"] is not None
        print(f"\n✓ User ID: {me['id']}")
        print(f"✓ Name: {me.get('name', 'N/A')}")
        print(f"✓ Email: {me.get('email', 'N/A')}")


@pytest.mark.asyncio
async def test_get_projects(api_token: str, token_type: str) -> None:
    """Test fetching projects."""
    async with aiohttp.ClientSession() as session:
        client = RailwayApiClient(api_token, session, token_type)
        projects = await client.async_get_projects()

        assert isinstance(projects, list)
        print(f"\n✓ Found {len(projects)} projects")

        for project in projects[:5]:  # Show first 5
            print(f"  - {project.get('name')} (ID: {project.get('id')})")


@pytest.mark.asyncio
async def test_get_teams(api_token: str, token_type: str) -> None:
    """Test fetching teams."""
    async with aiohttp.ClientSession() as session:
        client = RailwayApiClient(api_token, session, token_type)
        teams = await client.async_get_teams()

        assert isinstance(teams, list)
        print(f"\n✓ Found {len(teams)} teams")

        for team in teams:
            print(f"  - {team.get('name')} (ID: {team.get('id')})")


@pytest.mark.asyncio
async def test_get_customer(api_token: str, token_type: str) -> None:
    """Test fetching customer/billing information."""
    async with aiohttp.ClientSession() as session:
        client = RailwayApiClient(api_token, session, token_type)

        try:
            customer = await client.async_get_customer()
            print(f"\n✓ Customer ID: {customer.get('id', 'N/A')}")
            print(f"✓ Credit Balance: ${customer.get('creditBalance', 'N/A')}")
            print(f"✓ Billing Email: {customer.get('billingEmail', 'N/A')}")
            print(f"✓ State: {customer.get('state', 'N/A')}")
        except RailwayApiError as e:
            print(f"\n⚠ Customer info not available: {e}")
            # This is not a failure - some accounts may not have customer data
            pytest.skip("Customer data not available for this account")


@pytest.mark.asyncio
async def test_get_usage(api_token: str, token_type: str) -> None:
    """Test fetching usage information."""
    async with aiohttp.ClientSession() as session:
        client = RailwayApiClient(api_token, session, token_type)

        try:
            usage = await client.async_get_usage()
            print(f"\n✓ Current Usage: ${usage.get('currentUsage', 'N/A')}")
            print(f"✓ Estimated Usage: ${usage.get('estimatedUsage', 'N/A')}")
        except RailwayApiError as e:
            print(f"\n⚠ Usage info not available: {e}")
            pytest.skip("Usage data not available for this account")


@pytest.mark.asyncio
async def test_get_all_data(api_token: str, token_type: str) -> None:
    """Test fetching all data at once."""
    async with aiohttp.ClientSession() as session:
        client = RailwayApiClient(api_token, session, token_type)
        data = await client.async_get_all_data()

        assert "me" in data
        assert "projects" in data
        assert "teams" in data

        print("\n✓ All data fetched successfully:")
        print(f"  - User: {data['me'].get('name', data['me'].get('email', 'Unknown'))}")
        print(f"  - Projects: {len(data['projects'])}")
        print(f"  - Teams: {len(data['teams'])}")

        if data.get("customer"):
            print(f"  - Credit Balance: ${data['customer'].get('creditBalance', 'N/A')}")

        if data.get("usage"):
            print(f"  - Current Usage: ${data['usage'].get('currentUsage', 'N/A')}")


@pytest.mark.asyncio
async def test_invalid_token() -> None:
    """Test that invalid token raises auth error."""
    async with aiohttp.ClientSession() as session:
        client = RailwayApiClient("invalid_token_12345", session, "personal")

        with pytest.raises(RailwayAuthError):
            await client.async_get_me()

        print("\n✓ Invalid token correctly rejected")


@pytest.mark.asyncio
async def test_validate_token(api_token: str, token_type: str) -> None:
    """Test token validation."""
    async with aiohttp.ClientSession() as session:
        client = RailwayApiClient(api_token, session, token_type)
        is_valid = await client.async_validate_token()

        assert is_valid is True
        print("\n✓ Token is valid")
