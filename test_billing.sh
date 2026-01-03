#!/bin/bash
# Test billing/usage queries on Railway API

TOKEN="${1:-$RAILWAY_API_TOKEN}"

echo "Testing billing queries..."
echo ""

echo "=== Test: customer query ==="
curl -s -X POST https://backboard.railway.com/graphql/v2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"query { customer { id creditBalance billingEmail state } }"}' | python3 -m json.tool 2>/dev/null || cat

echo ""
echo "=== Test: usage query ==="
curl -s -X POST https://backboard.railway.com/graphql/v2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"query { usage { currentUsage estimatedUsage } }"}' | python3 -m json.tool 2>/dev/null || cat

echo ""
echo "=== Test: me with available fields ==="
curl -s -X POST https://backboard.railway.com/graphql/v2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"query { me { id name email agreedFairUse avatar banReason cost { current estimated } customer { id creditBalance state billingEmail } } }"}' | python3 -m json.tool 2>/dev/null || cat

echo ""
echo "=== Test: Schema introspection for billing types ==="
curl -s -X POST https://backboard.railway.com/graphql/v2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"query { __type(name: \"User\") { fields { name type { name kind ofType { name } } } } }"}' | python3 -m json.tool 2>/dev/null || cat

echo ""
