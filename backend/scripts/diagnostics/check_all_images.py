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

# Get all images
result = client.table('conversation_images').select('*').execute()
print(f"Total images in database: {len(result.data)}")
for img in result.data:
    print(f"\nConversation: {img['conversation_id']}")
    print(f"  Prompt: {img['prompt'][:50]}...")
    print(f"  Storage Path: {img['storage_path']}")
    print(f"  Generated: {img.get('generated_at', 'N/A')}")
