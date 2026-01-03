"""Pytest configuration and fixtures."""

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

# Load .env file from project root
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)


@pytest.fixture
def api_token() -> str:
    """Get the API token from environment."""
    token = os.getenv("RAILWAY_API_TOKEN")
    if not token or token == "your_token_here":
        pytest.skip("RAILWAY_API_TOKEN not set in .env file")
    return token


@pytest.fixture
def token_type() -> str:
    """Get the token type from environment."""
    return os.getenv("RAILWAY_TOKEN_TYPE", "personal")
