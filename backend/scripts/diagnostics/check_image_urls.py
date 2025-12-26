import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Load .env
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip().strip('"').strip("'")

from database import DatabaseService

db = DatabaseService.get_client()
result = db.table('conversation_images').select('*').execute()

for img in result.data:
    print(f"ID: {img['id']}")
    print(f"URL: {img['storage_url']}")
    print(f"Path: {img['storage_path']}")
    print(f"Created: {img['created_at']}")
    print()
