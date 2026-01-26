#!/bin/bash
# Manual API endpoint tests
# Usage: ./test_endpoints_manual.sh
# Or with dotenvx: dotenvx run -- ./test_endpoints_manual.sh

# Generate a token using the JWT secret from environment
generate_token() {
    python3 -c "
import os
import sys
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()

import jwt
from datetime import datetime, timezone, timedelta

secret = os.getenv('SUPABASE_JWT_SECRET')
if not secret:
    print('ERROR: SUPABASE_JWT_SECRET not set', file=sys.stderr)
    sys.exit(1)

payload = {
    'sub': 'test-user',
    'role': 'authenticated',
    'user_metadata': {'role': 'admin'},
    'iat': datetime.now(timezone.utc),
    'exp': datetime.now(timezone.utc) + timedelta(hours=1),
}
print(jwt.encode(payload, secret, algorithm='HS256'))
"
}

ADMIN_TOKEN=$(generate_token)

if [ -z "$ADMIN_TOKEN" ]; then
    echo "Failed to generate token. Make sure .env is configured."
    exit 1
fi

echo "========================================="
echo "Thesis API Endpoint Tests"
echo "========================================="
echo ""

echo "1. Root Endpoint (GET /):"
curl -s http://localhost:8000/
echo -e "\n"

echo "2. Admin Clients List (GET /api/clients):"
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" http://localhost:8000/api/clients | python3 -m json.tool 2>/dev/null || curl -s -H "Authorization: Bearer $ADMIN_TOKEN" http://localhost:8000/api/clients
echo -e "\n"

echo "3. Storage Info (GET /api/users/storage):"
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" http://localhost:8000/api/users/storage | python3 -m json.tool 2>/dev/null || curl -s -H "Authorization: Bearer $ADMIN_TOKEN" http://localhost:8000/api/users/storage
echo -e "\n"

echo "4. Conversations List (GET /api/conversations):"
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" http://localhost:8000/api/conversations | python3 -m json.tool 2>/dev/null | head -30 || curl -s -H "Authorization: Bearer $ADMIN_TOKEN" http://localhost:8000/api/conversations | head -30
echo -e "\n"

echo "5. Google Drive Status (GET /api/google-drive/status):"
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" http://localhost:8000/api/google-drive/status | python3 -m json.tool 2>/dev/null || curl -s -H "Authorization: Bearer $ADMIN_TOKEN" http://localhost:8000/api/google-drive/status
echo -e "\n"

echo "========================================="
echo "Tests Complete"
echo "========================================="
