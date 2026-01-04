"""Tests for Railway API client."""

import sys
from pathlib import Path

import aiohttp
import pytest

# Add the railway module directly to path
sys.path.insert(0, str(Path(__file__).parent.parent / "custom_components" / "railway"))

from api import (
    RailwayApiClient,
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


@pytest.mark.asyncio
async def test_get_projects(api_token: str, token_type: str) -> None:
    """Test fetching projects."""
    async with aiohttp.ClientSession() as session:
        client = RailwayApiClient(api_token, session, token_type)
        projects = await client.async_get_projects()

        assert isinstance(projects, list)


@pytest.mark.asyncio
async def test_get_all_data(api_token: str, token_type: str) -> None:
    """Test fetching all data at once."""
    async with aiohttp.ClientSession() as session:
        client = RailwayApiClient(api_token, session, token_type)
        data = await client.async_get_all_data()

        # Verify expected keys exist
        assert "me" in data
        assert "projects" in data
        assert "workspaces" in data
        assert "deployments" in data
        assert "earnings" in data

        # Verify data types
        assert isinstance(data["projects"], list)
        assert isinstance(data["workspaces"], list)
        assert isinstance(data["deployments"], dict)
        assert isinstance(data["earnings"], dict)

        # Verify earnings structure
        assert "templates_30d" in data["earnings"]
        assert "templates_total" in data["earnings"]
        assert "referrals_credited" in data["earnings"]
        assert "referrals_pending" in data["earnings"]


@pytest.mark.asyncio
async def test_invalid_token() -> None:
    """Test that invalid token raises auth error."""
    async with aiohttp.ClientSession() as session:
        client = RailwayApiClient("invalid_token_12345", session, "personal")

        with pytest.raises(RailwayAuthError):
            await client.async_get_me()


@pytest.mark.asyncio
async def test_validate_token(api_token: str, token_type: str) -> None:
    """Test token validation."""
    async with aiohttp.ClientSession() as session:
        client = RailwayApiClient(api_token, session, token_type)
        is_valid = await client.async_validate_token()

        assert is_valid is True
