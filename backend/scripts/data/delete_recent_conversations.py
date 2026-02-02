import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scripts.lib.credentials import get_credentials

creds = get_credentials()
SUPABASE_URL = creds["supabase_url"]
SUPABASE_SERVICE_ROLE_KEY = creds["supabase_key"]
CHARLIE_USER_ID = "d3ba5354-873a-435a-a36a-853373c4f6e5"

headers = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    "Content-Type": "application/json",
}

# IDs of the synthetic conversations we just created
conversation_ids = [
    "5658d465-e925-44e3-8349-9b0ab5b0b6fd",  # Investor Meeting Follow-Up
    "383ae9a2-0c26-4a61-995a-cf3491c91b5a",  # Leadership Team Meeting Agenda
    "d49654d4-ed72-458e-94b5-c27a0098690e",  # Strategic Time Allocation Review
    "f64fb0c2-c978-48cb-b510-5b8f5c79f791",  # Weekly Priority Triage
    "3ca63213-5c50-48e5-9381-3244ec8dd0ef",  # Investor Pitch Narrative
    "192c3536-98eb-4c75-a8e8-9e878e87699c",  # Board Update Memo
    "96c662cb-6707-4b66-89b4-f9bb07f92da1",  # Building Team Capacity
    "3f6a7678-b2bd-4ae3-82cc-df6628b12860",  # Delegation Audit
    "cff72e5a-01d2-4c4a-87b4-e861f41bda26",  # Framework for Partnership Evaluation
    "05431c09-ea20-4ff7-9cf9-7ca03938eb18",  # Reframing Product Roadmap
]

print(f"🗑️  Deleting {len(conversation_ids)} synthetic conversations...")
print()

for i, conv_id in enumerate(conversation_ids, 1):
    url = f"{SUPABASE_URL}/rest/v1/conversations"
    params = {"id": f"eq.{conv_id}"}

    response = requests.delete(url, headers=headers, params=params)

    if response.status_code == 204:
        print(f"[{i}/{len(conversation_ids)}] ✅ Deleted {conv_id}")
    else:
        print(f"[{i}/{len(conversation_ids)}] ❌ Error deleting {conv_id}: {response.status_code}")

print()
print("✅ Deletion complete")
