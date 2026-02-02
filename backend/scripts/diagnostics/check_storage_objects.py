import os
from pathlib import Path

env_file = Path(__file__).parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip().strip('"').strip("'")

from supabase import create_client

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
client = create_client(url, key)

# Query the storage.objects table directly
result = client.table("objects").select("*").eq("bucket_id", "conversation-images").execute()

print(f"Storage.objects table: {len(result.data)} files\n")

for obj in result.data:
    print(f"Path: {obj['name']}")
    print(f"  Size: {obj.get('metadata', {}).get('size', 'unknown')} bytes")
    print(f"  Created: {obj.get('created_at', 'unknown')}")
    print()
