"""Fix existing image URLs in database that point to gygax-files.com.

Update them to use direct Supabase storage URLs.
"""

import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

# Load .env
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip().strip('"').strip("'")

from database import DatabaseService


def fix_image_urls():
    """Fix all image URLs in the database."""
    db = DatabaseService.get_client()
    supabase_url = os.getenv("SUPABASE_URL")

    # Get all images
    result = db.table("conversation_images").select("*").execute()
    images = result.data

    print(f"Found {len(images)} images in database")

    fixed_count = 0
    for image in images:
        storage_url = image["storage_url"]

        # Check if it's a gygax URL
        if "gygax-files.com" in storage_url:
            # Extract the path after /d/
            # Example: https://gygax-files.com/d/UUID.png -> UUID.png
            # But we need the full storage path which is in storage_path field
            storage_path = image["storage_path"]

            # Construct new URL
            new_url = f"{supabase_url}/storage/v1/object/public/conversation-images/{storage_path}"

            # Update in database
            db.table("conversation_images").update({"storage_url": new_url}).eq(
                "id", image["id"]
            ).execute()

            print(f"✅ Fixed image {image['id'][:8]}: {storage_url[:50]}... -> {new_url[:70]}...")
            fixed_count += 1

    print(f"\n✅ Fixed {fixed_count} image URLs")
    return fixed_count


if __name__ == "__main__":
    fix_image_urls()
