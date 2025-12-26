import os
from pathlib import Path

# Load .env
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

# List all files in conversation-images bucket
files = client.storage.from_('conversation-images').list()

def list_recursive(path='', level=0):
    items = client.storage.from_('conversation-images').list(path)
    for item in items:
        indent = '  ' * level
        item_path = f"{path}/{item['name']}" if path else item['name']

        if item.get('id'):  # It's a file
            print(f"{indent}📄 {item['name']} ({item.get('metadata', {}).get('size', 0)} bytes)")
        else:  # It's a folder
            print(f"{indent}📁 {item['name']}/")
            list_recursive(item_path, level + 1)

print("Storage bucket contents:\n")
list_recursive()
