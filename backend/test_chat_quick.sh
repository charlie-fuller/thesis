#!/bin/bash
# Quick chat endpoint test
# Usage: ./test_chat_quick.sh
# Or with dotenvx: dotenvx run -- ./test_chat_quick.sh

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

echo "=== Testing Chat Endpoint ==="
echo ""
echo "Sending chat message..."
curl -s -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, can you help me?",
    "use_knowledge_base": true,
    "max_chunks": 3
  }' | python3 -m json.tool 2>/dev/null | head -50

echo ""
echo "=== Chat Test Complete ==="
