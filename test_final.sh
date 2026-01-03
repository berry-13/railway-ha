#!/bin/bash
# Test the correct billing queries

TOKEN="${1:-$RAILWAY_API_TOKEN}"

echo "=== Get workspaces with billing ==="
curl -s -X POST https://backboard.railway.com/graphql/v2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"query { me { workspaces { id name customer { id billingEmail state creditBalance defaultPaymentMethod { id } } plan { id name } } } }"}' | python3 -m json.tool 2>/dev/null || cat

echo ""
echo "=== Customer type fields ==="
curl -s -X POST https://backboard.railway.com/graphql/v2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"query { __type(name: \"Customer\") { fields { name type { name kind ofType { name } } } } }"}' | python3 -m json.tool 2>/dev/null || cat

echo ""
echo "=== estimatedUsage query ==="
curl -s -X POST https://backboard.railway.com/graphql/v2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"query { __type(name: \"Query\") { fields(includeDeprecated: true) { name args { name type { name kind ofType { name } } } } } }"}' 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); fields=[f for f in d['data']['__type']['fields'] if 'usage' in f['name'].lower() or 'estimated' in f['name'].lower()]; print(json.dumps(fields, indent=2))"

echo ""
