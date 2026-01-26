import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scripts.lib.credentials import get_credentials

creds = get_credentials()
SUPABASE_URL = creds['supabase_url']
SUPABASE_SERVICE_ROLE_KEY = creds['supabase_key']
CHARLIE_USER_ID = "d3ba5354-873a-435a-a36a-853373c4f6e5"

headers = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    "Content-Type": "application/json"
}

# Get all conversations for Charlie created today
url = f"{SUPABASE_URL}/rest/v1/conversations"
params = {
    "user_id": f"eq.{CHARLIE_USER_ID}",
    "select": "id,title,created_at",
    "order": "created_at.desc",
    "limit": 20
}

response = requests.get(url, headers=headers, params=params)

if response.status_code == 200:
    conversations = response.json()

    # Filter to only synthetic ones (created recently - within last hour)
    now = datetime.now(timezone.utc)
    synthetic_titles = [
        "Weekly Team Meeting Scheduling",
        "Investor Meeting Prep",
        "Partnership Evaluation Framework",
        "Hiring Priority Analysis",
        "Vision Document for Team",
        "Board Update Email",
        "Developmental Feedback for Marcus",
        "Career Development Plan for Sarah",
        "Weekly Priority Check",
        "Strategic Time Audit"
    ]

    to_delete = []
    for conv in conversations:
        if conv['title'] in synthetic_titles:
            to_delete.append(conv)

    print(f"🗑️  Found {len(to_delete)} synthetic conversations to delete")
    print()

    for i, conv in enumerate(to_delete, 1):
        print(f"[{i}/{len(to_delete)}] Deleting: {conv['title']}")

        # Delete conversation (cascades to messages)
        delete_url = f"{SUPABASE_URL}/rest/v1/conversations"
        delete_params = {
            "id": f"eq.{conv['id']}"
        }

        delete_response = requests.delete(delete_url, headers=headers, params=delete_params)

        if delete_response.status_code == 204:
            print(f"   ✅ Deleted conversation {conv['id']}")
        else:
            print(f"   ❌ Error deleting: {delete_response.status_code}")
            print(f"   {delete_response.text}")
        print()

    print(f"✅ Deleted {len(to_delete)} synthetic conversations")
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)
