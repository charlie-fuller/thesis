"""Backfill database records for images that exist in storage but not in conversation_images table"""

import os
from datetime import datetime
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

# Get existing database records
db_result = client.table("conversation_images").select("storage_path").execute()
existing_paths = {img["storage_path"] for img in db_result.data}
print(f"Found {len(existing_paths)} existing database records")


# Scan storage bucket
def scan_storage(path=""):
    items = client.storage.from_("conversation-images").list(path)
    files = []
    for item in items:
        item_path = f"{path}/{item['name']}" if path else item["name"]

        if item.get("id"):  # It's a file
            files.append(
                {
                    "path": item_path,
                    "size": item.get("metadata", {}).get("size", 0),
                    "name": item["name"],
                }
            )
        else:  # It's a folder - recurse
            files.extend(scan_storage(item_path))

    return files


print("\nScanning storage bucket...")
storage_files = scan_storage()
print(f"Found {len(storage_files)} files in storage")

# Find files missing from database
missing_files = [f for f in storage_files if f["path"] not in existing_paths]
print(f"\nFound {len(missing_files)} files missing database records")

if not missing_files:
    print("✅ All storage files have database records!")
else:
    print("\nCreating database records...")

    for file in missing_files:
        # Parse path: user_id/conversation_id/filename.ext
        parts = file["path"].split("/")
        if len(parts) != 3:
            print(f"⚠️  Skipping invalid path: {file['path']}")
            continue

        user_id, conversation_id, filename = parts

        # Construct public URL
        storage_url = f"{url}/storage/v1/object/public/conversation-images/{file['path']}"

        # Extract file extension
        file_ext = filename.split(".")[-1]
        mime_type = f"image/{file_ext}"

        # Create database record
        record = {
            "conversation_id": conversation_id,
            "message_id": None,
            "prompt": "(Backfilled - image from storage)",
            "aspect_ratio": "16:9",  # Default
            "model": "gemini-2.5-flash-image",  # Assume this model
            "storage_url": storage_url,
            "storage_path": file["path"],
            "mime_type": mime_type,
            "file_size": file["size"],
            "metadata": {"backfilled": True, "backfill_date": datetime.now().isoformat()},
        }

        try:
            result = client.table("conversation_images").insert(record).execute()
            if result.data:
                print(f"✅ Created record for: {file['path']}")
        except Exception as e:
            print(f"❌ Failed to create record for {file['path']}: {e}")

print("\n✅ Backfill complete!")

# Verify
final_result = client.table("conversation_images").select("*").execute()
print(f"\nTotal images in database now: {len(final_result.data)}")
