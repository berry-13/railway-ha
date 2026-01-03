#!/bin/bash
# Explore Railway API schema for billing/usage

TOKEN="${1:-$RAILWAY_API_TOKEN}"

echo "=== Workspaces query ==="
curl -s -X POST https://backboard.railway.com/graphql/v2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"query { me { workspaces { edges { node { id name team { id name } } } } } }"}' | python3 -m json.tool 2>/dev/null || cat

echo ""
echo "=== Team type fields ==="
curl -s -X POST https://backboard.railway.com/graphql/v2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"query { __type(name: \"Team\") { fields { name type { name kind ofType { name } } } } }"}' | python3 -m json.tool 2>/dev/null || cat

echo ""
echo "=== Workspace type fields ==="
curl -s -X POST https://backboard.railway.com/graphql/v2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"query { __type(name: \"Workspace\") { fields { name type { name kind ofType { name } } } } }"}' | python3 -m json.tool 2>/dev/null || cat

echo ""
echo "=== Query root fields (what queries exist) ==="
curl -s -X POST https://backboard.railway.com/graphql/v2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"query { __type(name: \"Query\") { fields { name } } }"}' | python3 -m json.tool 2>/dev/null || cat

echo ""
