#!/bin/bash
# Quick curl test for Railway API
# Usage: ./test_curl.sh YOUR_TOKEN_HERE

TOKEN="${1:-$RAILWAY_API_TOKEN}"

if [ -z "$TOKEN" ]; then
    echo "Usage: ./test_curl.sh YOUR_TOKEN"
    echo "Or set RAILWAY_API_TOKEN environment variable"
    exit 1
fi

echo "Testing Railway API with token: ${TOKEN:0:8}...${TOKEN: -4}"
echo ""

echo "=== Test 1: me query (Personal Token) ==="
curl -s -X POST https://backboard.railway.com/graphql/v2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"query { me { id name email } }"}' | python3 -m json.tool 2>/dev/null || cat

echo ""
echo "=== Test 2: projects query ==="
curl -s -X POST https://backboard.railway.com/graphql/v2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"query { projects { edges { node { id name } } } }"}' | python3 -m json.tool 2>/dev/null || cat

echo ""
echo "=== Test 3: Introspection query (check if API responds) ==="
curl -s -X POST https://backboard.railway.com/graphql/v2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"query { __typename }"}' | python3 -m json.tool 2>/dev/null || cat

echo ""
echo "=== Test 4: Check without token ==="
curl -s -X POST https://backboard.railway.com/graphql/v2 \
  -H "Content-Type: application/json" \
  -d '{"query":"query { __typename }"}' | python3 -m json.tool 2>/dev/null || cat

echo ""
