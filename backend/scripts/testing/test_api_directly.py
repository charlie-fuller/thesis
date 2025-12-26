"""
Direct API test - no imports from services
"""
import base64
import json
import os
from pathlib import Path

import requests

# Load .env
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip().strip('"').strip("'")

api_key = os.getenv("GOOGLE_GENERATIVE_AI_API_KEY")
print(f"API Key: {api_key[:15]}...{api_key[-5:]}")

# Test parameters
model_name = "gemini-2.5-flash-image"
base_url = "https://generativelanguage.googleapis.com/v1beta"
prompt = "A happy dog catching a frisbee in a park"

# Construct API call
url = f"{base_url}/models/{model_name}:generateContent"
headers = {
    "x-goog-api-key": api_key,
    "Content-Type": "application/json"
}
payload = {
    "contents": [{
        "parts": [
            {"text": prompt}
        ]
    }]
}

print(f"\nCalling: {url}")
print(f"Prompt: {prompt}")
print("\nSending request...")

response = requests.post(url, headers=headers, json=payload, timeout=60)

print(f"\nStatus: {response.status_code}")

if response.status_code != 200:
    print(f"Error: {response.text}")
else:
    data = response.json()

    # Print full response structure for debugging
    print("\nResponse structure:")
    print(json.dumps(data, indent=2)[:1000])

    # Try to extract image
    if "candidates" in data and len(data["candidates"]) > 0:
        candidate = data["candidates"][0]

        if "content" in candidate and "parts" in candidate["content"]:
            for part in candidate["content"]["parts"]:
                if "inlineData" in part:
                    inline_data = part["inlineData"]
                    if "data" in inline_data:
                        image_data = inline_data["data"]
                        print(f"\n✅ SUCCESS! Got image data: {len(image_data)} chars")

                        # Save it
                        image_bytes = base64.b64decode(image_data)
                        output_path = Path(__file__).parent / "test_direct_api.png"
                        output_path.write_bytes(image_bytes)
                        print(f"💾 Saved to: {output_path}")
                        print(f"File size: {len(image_bytes):,} bytes")
                    else:
                        print("\n❌ No 'data' in inlineData")
                else:
                    print(f"\nPart type: {list(part.keys())}")
        else:
            print("\n❌ No content/parts in candidate")
    else:
        print("\n❌ No candidates in response")
