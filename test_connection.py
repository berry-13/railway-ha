#!/usr/bin/env python3
"""
Quick test script to verify Railway API connection.

Usage:
    1. Copy .env.example to .env
    2. Add your Railway API token to .env
    3. Run: python test_connection.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Note: python-dotenv not installed, reading from environment only")

# Add custom_components to path
sys.path.insert(0, str(Path(__file__).parent / "custom_components" / "railway"))

import aiohttp

from api import (
    RailwayApiClient,
    RailwayApiError,
    RailwayAuthError,
    RailwayConnectionError,
)


async def test_connection():
    """Test the Railway API connection."""
    token = os.getenv("RAILWAY_API_TOKEN")
    token_type = os.getenv("RAILWAY_TOKEN_TYPE", "personal")

    if not token or token == "your_token_here":
        print("❌ Error: RAILWAY_API_TOKEN not set")
        print("\nTo fix this:")
        print("  1. Copy .env.example to .env")
        print("  2. Replace 'your_token_here' with your actual Railway API token")
        print("  3. Get a token at: https://railway.com/account/tokens")
        print("  4. IMPORTANT: Select 'No workspace' when creating the token!")
        return False

    print("Testing Railway API connection...")
    print(f"Token type: {token_type}")
    print(f"Token: {token[:8]}...{token[-4:]}")
    print("-" * 50)

    async with aiohttp.ClientSession() as session:
        client = RailwayApiClient(token, session, token_type)

        # Test 1: Get user info
        print("\n1. Testing user info (me query)...")
        try:
            me = await client.async_get_me()
            if me and me.get("id"):
                print(f"   ✓ User ID: {me['id']}")
                print(f"   ✓ Name: {me.get('name', 'N/A')}")
                print(f"   ✓ Email: {me.get('email', 'N/A')}")
            else:
                print(f"   ❌ No user data returned: {me}")
                return False
        except RailwayAuthError as e:
            print(f"   ❌ Authentication failed: {e}")
            print("\n   Possible causes:")
            print("   - Token is invalid or expired")
            print("   - Token was created WITH a workspace selected")
            print("   - Create a new token with 'No workspace' selected")
            return False
        except RailwayConnectionError as e:
            print(f"   ❌ Connection failed: {e}")
            return False
        except RailwayApiError as e:
            print(f"   ❌ API error: {e}")
            return False

        # Test 2: Get workspaces with billing
        print("\n2. Testing workspaces with billing...")
        try:
            me_with_ws = await client.async_get_me_with_workspaces()
            workspaces = me_with_ws.get("workspaces", [])
            print(f"   ✓ Found {len(workspaces)} workspaces")
            for ws in workspaces:
                print(f"     - {ws.get('name')} (ID: {ws.get('id', 'N/A')[:8]}...)")
                customer = ws.get("customer", {})
                if customer:
                    print(f"       Credit Balance: ${customer.get('creditBalance', 'N/A')}")
                    print(f"       Current Usage: ${customer.get('currentUsage', 'N/A')}")
                    print(f"       State: {customer.get('state', 'N/A')}")
                    if customer.get("isTrialing"):
                        print(f"       Trial Days Remaining: {customer.get('trialDaysRemaining', 'N/A')}")
        except RailwayApiError as e:
            print(f"   ⚠ Workspaces query failed: {e}")

        # Test 3: Get projects
        print("\n3. Testing projects query...")
        try:
            projects = await client.async_get_projects()
            print(f"   ✓ Found {len(projects)} projects")
            for p in projects[:3]:
                pid = p.get('id', '')
                print(f"     - {p.get('name')} ({pid[:8] if pid else 'N/A'}...)")
            if len(projects) > 3:
                print(f"     ... and {len(projects) - 3} more")
        except RailwayApiError as e:
            print(f"   ⚠ Projects query failed: {e}")

        # Test 4: Get all data (full integration test)
        print("\n4. Testing full data fetch...")
        try:
            all_data = await client.async_get_all_data()
            print(f"   ✓ User: {all_data.get('me', {}).get('name', 'N/A')}")
            print(f"   ✓ Workspaces: {len(all_data.get('workspaces', []))}")
            print(f"   ✓ Projects: {len(all_data.get('projects', []))}")
            print(f"   ✓ Templates: {len(all_data.get('templates', []))}")

            # Show billing summary
            total_credits = 0.0
            total_usage = 0.0
            for ws in all_data.get("workspaces", []):
                customer = ws.get("customer", {})
                if customer.get("creditBalance"):
                    total_credits += customer["creditBalance"]
                if customer.get("currentUsage"):
                    total_usage += customer["currentUsage"]

            if total_credits or total_usage:
                print(f"   ✓ Total Credit Balance: ${total_credits:.2f}")
                print(f"   ✓ Total Current Usage: ${total_usage:.2f}")

            # Show earnings summary
            earnings = all_data.get("earnings", {})
            if earnings:
                print("\n   📊 Earnings Summary:")
                print(f"      Templates (30d): ${earnings.get('templates_30d', 0):.2f}")
                print(f"      Templates Total: ${earnings.get('templates_total', 0):.2f}")
                print(f"      Templates Payout: ${earnings.get('templates_payout', 0):.2f}")
                print(f"      Referrals Credited: {earnings.get('referrals_credited', 0)}")
                print(f"      Referrals Pending: {earnings.get('referrals_pending', 0)}")
                print("      Note: Available Balance not accessible via API")

            # Show template details
            templates = all_data.get("templates", [])
            if templates:
                print("\n   📦 Templates:")
                for t in templates:
                    metrics = all_data.get("template_metrics", {}).get(t.get("id"), {})
                    print(f"      - {t.get('name')} (code: {t.get('code')})")
                    print(f"        Total Payout: ${t.get('totalPayout', 0):.2f}")
                    if metrics:
                        print(f"        Earnings (30d): ${metrics.get('earningsLast30Days', 0):.2f}")
                        print(f"        Total Earnings: ${metrics.get('totalEarnings', 0):.2f}")
                        print(f"        Active Deployments: {metrics.get('activeDeployments', 0)}")
        except RailwayApiError as e:
            print(f"   ⚠ Full data fetch failed: {e}")

        print("\n" + "=" * 50)
        print("✅ Connection test PASSED!")
        print("=" * 50)
        print("\nYour token is working. You can now use the integration in Home Assistant.")
        print("\nTo use in Home Assistant:")
        print("  1. Copy custom_components/railway to your HA config/custom_components/")
        print("  2. Restart Home Assistant")
        print("  3. Add the Railway integration via Settings > Devices & Services")
        return True


if __name__ == "__main__":
    success = asyncio.run(test_connection())
    sys.exit(0 if success else 1)
