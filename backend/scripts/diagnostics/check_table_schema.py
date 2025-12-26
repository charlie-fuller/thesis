import os
from pathlib import Path

env_file = Path(__file__).parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip().strip('"').strip("'")

from supabase import create_client

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
client = create_client(url, key)

# Try to get table info - this will show us what fields exist
try:
    result = client.table('conversation_images').select('*').limit(1).execute()
    if result.data:
        print("Table fields:", list(result.data[0].keys()))
except Exception as e:
    print(f"Error: {e}")
