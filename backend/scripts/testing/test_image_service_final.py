"""
Final integration test for the updated ImageGenerationService.
Tests the HTTP REST API implementation.
"""
import asyncio
import base64
import os
import sys
from pathlib import Path

# Setup path
sys.path.insert(0, str(Path(__file__).parent))

# Load env
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip().strip('"').strip("'")

from services.image_generation import ImageGenerationService


async def test_single_image():
    """Test generating a single image."""
    print("=" * 70)
    print("TEST 1: Single Image Generation")
    print("=" * 70)

    try:
        service = ImageGenerationService()
        print(f"✅ Service initialized (model: {service.model_name})")

        prompt = "A futuristic AI assistant robot in a modern office, digital art style"
        print(f"\n📝 Prompt: {prompt}")
        print("\n⏳ Generating image...")

        result = await service.generate_image(prompt)

        if result.get("success"):
            print("\n✅ SUCCESS!")
            print(f"   Model: {result['model']}")
            print(f"   MIME: {result['mime_type']}")
            print(f"   Data size: {len(result['image_data'])} chars (base64)")

            # Save image
            image_bytes = base64.b64decode(result['image_data'])
            output_path = Path(__file__).parent / "test_single_output.png"
            output_path.write_bytes(image_bytes)

            print(f"\n💾 Saved to: {output_path}")
            print(f"   File size: {len(image_bytes):,} bytes")

            return True
        else:
            print(f"\n❌ Failed: {result}")
            return False

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False


async def test_batch_images():
    """Test generating multiple images."""
    print("\n" + "=" * 70)
    print("TEST 2: Batch Image Generation")
    print("=" * 70)

    try:
        service = ImageGenerationService()

        prompts = [
            "A happy robot holding a lightbulb, cartoon style",
            "A peaceful zen garden with cherry blossoms, watercolor style"
        ]

        print(f"\n📝 Generating {len(prompts)} images...")
        for i, p in enumerate(prompts, 1):
            print(f"   {i}. {p}")

        print("\n⏳ Processing batch...")
        results = await service.generate_multiple_images(prompts)

        successful = 0
        for i, result in enumerate(results, 1):
            if result.get("success"):
                print(f"\n✅ Image {i}: SUCCESS")
                successful += 1

                # Save image
                image_bytes = base64.b64decode(result['image_data'])
                output_path = Path(__file__).parent / f"test_batch_{i}.png"
                output_path.write_bytes(image_bytes)
                print(f"   💾 Saved: {output_path}")
                print(f"   Size: {len(image_bytes):,} bytes")
            else:
                print(f"\n❌ Image {i}: FAILED")
                print(f"   Error: {result.get('error', 'Unknown')}")

        print(f"\n📊 Batch result: {successful}/{len(prompts)} successful")

        return successful == len(prompts)

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False


async def main():
    """Run all tests."""
    print("\n🚀 THESIS IMAGE SERVICE INTEGRATION TEST\n")

    # Check API key
    api_key = os.getenv("GOOGLE_GENERATIVE_AI_API_KEY")
    if not api_key:
        print("❌ ERROR: GOOGLE_GENERATIVE_AI_API_KEY not set")
        return

    print(f"✅ API Key configured: {api_key[:15]}...{api_key[-5:]}\n")

    # Run tests
    test1_passed = await test_single_image()
    test2_passed = await test_batch_images()

    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    print(f"Single image:    {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Batch images:    {'✅ PASSED' if test2_passed else '❌ FAILED'}")

    if test1_passed and test2_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("\n✨ Image generation service is ready to use!")
        print("   • Updated to use HTTP REST API")
        print("   • Working with gemini-2.5-flash-image (nano banana)")
        print("   • Ready for production use")
    else:
        print("\n⚠️  Some tests failed - please review errors above")

    print()


if __name__ == "__main__":
    asyncio.run(main())
