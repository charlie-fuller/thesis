"""
Test script for Google Gemini image generation (Nano Banana).
"""
import asyncio
import base64
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from services.image_generation import ImageGenerationService


async def test_image_generation():
    """Test basic image generation."""
    print("🎨 Testing Google Gemini Image Generation (Nano Banana)")
    print("=" * 60)

    # Check for API key
    api_key = os.getenv("GOOGLE_GENERATIVE_AI_API_KEY")
    if not api_key:
        print("❌ ERROR: GOOGLE_GENERATIVE_AI_API_KEY not set")
        return False

    print(f"✅ API Key found: {api_key[:10]}...{api_key[-5:]}")

    try:
        # Initialize service
        print("\n📦 Initializing ImageGenerationService...")
        service = ImageGenerationService()
        print(f"✅ Service initialized with model: {service.model_name}")

        # Test prompt
        test_prompt = "A futuristic robot assistant named Thesis helping a user at a computer, photorealistic style"
        print(f"\n🖼️  Test prompt: {test_prompt}")

        # Generate image
        print("\n⏳ Generating image...")
        result = await service.generate_image(test_prompt)

        if result.get("success"):
            print("\n✅ SUCCESS! Image generated")
            print(f"   Model: {result['model']}")
            print(f"   MIME Type: {result['mime_type']}")
            print(f"   Image data size: {len(result['image_data'])} characters (base64)")

            # Save image to file for verification
            output_path = Path(__file__).parent / "test_output_image.png"
            image_bytes = base64.b64decode(result['image_data'])
            output_path.write_bytes(image_bytes)
            print(f"\n💾 Image saved to: {output_path}")
            print(f"   File size: {len(image_bytes)} bytes")

            return True
        else:
            print(f"\n❌ Generation failed: {result}")
            return False

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_batch_generation():
    """Test batch image generation."""
    print("\n" + "=" * 60)
    print("🎨 Testing Batch Image Generation")
    print("=" * 60)

    try:
        service = ImageGenerationService()

        prompts = [
            "A simple red circle on white background",
            "A blue square with rounded corners"
        ]

        print(f"\n🖼️  Generating {len(prompts)} images...")
        results = await service.generate_multiple_images(prompts)

        successful = sum(1 for r in results if r.get("success"))
        print(f"\n✅ Batch complete: {successful}/{len(prompts)} successful")

        for i, result in enumerate(results):
            if result.get("success"):
                print(f"   ✓ Image {i+1}: Generated successfully")
            else:
                print(f"   ✗ Image {i+1}: {result.get('error', 'Unknown error')}")

        return successful == len(prompts)

    except Exception as e:
        print(f"\n❌ Batch test error: {str(e)}")
        return False


async def main():
    """Run all tests."""
    print("\n" + "🚀 THESIS IMAGE GENERATION TEST " + "\n")

    # Load environment variables
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        print(f"📄 Loading environment from: {env_file}")
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
    else:
        print("⚠️  No .env file found, using system environment variables")

    # Run tests
    test1_passed = await test_image_generation()

    if test1_passed:
        test2_passed = await test_batch_generation()
    else:
        print("\n⏭️  Skipping batch test due to basic test failure")
        test2_passed = False

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Basic generation: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Batch generation: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
