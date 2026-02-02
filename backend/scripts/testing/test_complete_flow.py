"""Test the complete image generation flow end-to-end."""

import asyncio
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
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip().strip('"').strip("'")

from database import DatabaseService
from services.image_generation import get_image_generation_service
from services.storage_service import get_storage_service


async def test_complete_flow():
    print("=" * 70)
    print("COMPLETE IMAGE GENERATION FLOW TEST")
    print("=" * 70)

    # Test data
    user_id = "test-user-" + os.urandom(4).hex()
    conversation_id = "test-conv-" + os.urandom(4).hex()
    prompt = "A happy robot waving hello"

    print("\n📝 Test Configuration:")
    print(f"   User ID: {user_id}")
    print(f"   Conversation ID: {conversation_id}")
    print(f"   Prompt: {prompt}")

    try:
        # Step 1: Generate image
        print("\n🎨 Step 1: Generating image...")
        image_service = get_image_generation_service()
        result = await image_service.generate_image(
            prompt=prompt, model="fast", aspect_ratio="16:9"
        )

        if not result.get("success"):
            print(f"❌ Image generation failed: {result}")
            return False

        print(f"✅ Image generated: {len(result['image_data'])} bytes (base64)")
        print(f"   Model: {result['model']}")
        print(f"   MIME: {result['mime_type']}")

        # Step 2: Upload to storage
        print("\n☁️  Step 2: Uploading to storage...")
        storage_service = get_storage_service()
        mime_type = result["mime_type"]
        file_ext = mime_type.split("/")[-1] if "/" in mime_type else "png"

        upload_result = storage_service.upload_image(
            image_data=result["image_data"],
            user_id=user_id,
            conversation_id=conversation_id,
            file_extension=file_ext,
        )

        if not upload_result:
            print("❌ Storage upload failed")
            return False

        print("✅ Uploaded to storage")
        print(f"   URL: {upload_result['storage_url'][:80]}...")
        print(f"   Path: {upload_result['storage_path']}")
        print(f"   Size: {upload_result['file_size']:,} bytes")

        # Verify URL format
        if "gygax-files.com" in upload_result["storage_url"]:
            print("❌ ERROR: URL still using gygax-files.com CDN!")
            return False
        elif "supabase.co/storage/v1/object/public" in upload_result["storage_url"]:
            print("✅ URL format correct (direct Supabase URL)")
        else:
            print("⚠️  WARNING: Unexpected URL format")

        # Step 3: Create temporary conversation for testing
        print("\n💾 Step 3: Creating test conversation...")
        db = DatabaseService.get_client()

        # Create a temporary conversation record
        conv_record = {
            "id": conversation_id,
            "user_id": user_id,
            "title": "Test Conversation",
            "metadata": {"test": True},
        }

        conv_result = db.table("conversations").insert(conv_record).execute()
        if not conv_result.data:
            print("❌ Failed to create test conversation")
            return False

        print("✅ Test conversation created")

        # Step 4: Store image metadata in database
        print("\n💾 Step 4: Storing image metadata in database...")
        image_record = {
            "conversation_id": conversation_id,
            "message_id": None,
            "prompt": prompt,
            "aspect_ratio": "16:9",
            "model": result["model"],
            "storage_url": upload_result["storage_url"],
            "storage_path": upload_result["storage_path"],
            "mime_type": upload_result["content_type"],
            "file_size": upload_result["file_size"],
            "metadata": {
                "model_key": result.get("model_key"),
                "enhanced_prompt": result.get("enhanced_prompt"),
                "test": True,
            },
        }

        insert_result = db.table("conversation_images").insert(image_record).execute()
        if not insert_result.data:
            print("❌ Failed to store image metadata")
            return False

        stored_image = insert_result.data[0]
        print("✅ Image metadata stored")
        print(f"   Image ID: {stored_image['id']}")

        # Step 5: Verify retrieval
        print("\n🔍 Step 5: Verifying image retrieval...")
        retrieve_result = (
            db.table("conversation_images")
            .select("*")
            .eq("conversation_id", conversation_id)
            .execute()
        )

        if not retrieve_result.data or len(retrieve_result.data) == 0:
            print("❌ Failed to retrieve image")
            return False

        retrieved_image = retrieve_result.data[0]
        print("✅ Image retrieved successfully")
        print(f"   URL: {retrieved_image['storage_url'][:80]}...")

        # Cleanup
        print("\n🧹 Cleanup: Removing test data...")
        db.table("conversation_images").delete().eq("conversation_id", conversation_id).execute()
        db.table("conversations").delete().eq("id", conversation_id).execute()
        storage_service.delete_conversation_images(user_id, conversation_id)
        print("✅ Test data cleaned up")

        # Success!
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        print("\n🎉 Complete image generation flow is working correctly!")
        print("\nVerified:")
        print("  ✅ Image generation via Gemini API")
        print("  ✅ Storage upload to Supabase")
        print("  ✅ Correct URL format (no gygax-files.com)")
        print("  ✅ Database insertion")
        print("  ✅ Image retrieval")
        print("\nReady for production testing!\n")

        return True

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    asyncio.run(test_complete_flow())
