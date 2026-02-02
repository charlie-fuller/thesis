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

# Strategic keywords
strategic_keywords = [
    "conceptual",
    "model",
    "framework",
    "strategy",
    "plan",
    "draft",
    "report",
    "brief",
    "memo",
]

# Get all Charlie's conversations
url = f"{SUPABASE_URL}/rest/v1/conversations"
params = {"user_id": f"eq.{CHARLIE_USER_ID}", "select": "id"}

response = requests.get(url, headers=headers, params=params)
conversation_ids = [c["id"] for c in response.json()]

print(f"📊 Total conversations: {len(conversation_ids)}\n")

# Check each conversation for strategic keywords
strategic_count = 0

for conv_id in conversation_ids:
    # Get first user message
    msgs_url = f"{SUPABASE_URL}/rest/v1/messages"
    msg_params = {
        "conversation_id": f"eq.{conv_id}",
        "role": "eq.user",
        "select": "content",
        "order": "timestamp.asc",
        "limit": "1",
    }

    msg_response = requests.get(msgs_url, headers=headers, params=msg_params)

    if msg_response.status_code == 200 and msg_response.json():
        first_msg = msg_response.json()[0]
        content_lower = first_msg["content"].lower()

        # Check for keywords
        has_keyword = any(kw in content_lower for kw in strategic_keywords)

        if has_keyword:
            strategic_count += 1

print(f"✅ Strategic conversations detected: {strategic_count}")
print(f"📈 Ideation Velocity (if 1 week): {strategic_count:.1f} drafts/week")
print("🎯 Goal: ≥2 drafts/week")
print(f"Status: {'✅ EXCEEDS GOAL' if strategic_count >= 2 else '❌ BELOW GOAL'}")
print()

# Calculate Correction Loop
total_turns = 0
convo_count = 0

for conv_id in conversation_ids:
    # Count user messages
    turn_params = {"conversation_id": f"eq.{conv_id}", "role": "eq.user", "select": "id"}

    turn_response = requests.get(msgs_url, headers=headers, params=turn_params)

    if turn_response.status_code == 200:
        num_turns = len(turn_response.json())
        if num_turns > 0:
            total_turns += num_turns
            convo_count += 1

if convo_count > 0:
    avg_turns = total_turns / convo_count
    print("🔄 Correction Loop Efficiency:")
    print(f"  Conversations analyzed: {convo_count}")
    print(f"  Average turns: {avg_turns:.1f}")
    print("  Goal: <2 turns")
    print(f"  Status: {'✅ MET' if avg_turns < 2 else '⚠️ NEEDS IMPROVEMENT'}")
