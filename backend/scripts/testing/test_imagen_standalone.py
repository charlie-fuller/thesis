"""Standalone test for Google Gemini image generation (Nano Banana).

No dependencies on other services.
"""

import asyncio
import base64
import os
from pathlib import Path

import google.generativeai as genai


async def test_image_generation():
    """Test image generation with Google Gemini."""
    print("🎨 Testing Google Gemini Image Generation (Nano Banana)")
    print("=" * 70)

    # Load .env file
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        print(f"📄 Loading environment from: {env_file}")
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip().strip('"').strip("'")
    else:
        print("⚠️  No .env file found")

    # Check for API key
    api_key = os.getenv("GOOGLE_GENERATIVE_AI_API_KEY")
    if not api_key:
        print("❌ ERROR: GOOGLE_GENERATIVE_AI_API_KEY not set in environment")
        return False

    print(f"✅ API Key found: {api_key[:15]}...{api_key[-5:]}")
    print()

    try:
        # Configure API
        print("🔧 Configuring Google Generative AI...")
        genai.configure(api_key=api_key)

        # Try the model
        model_name = "gemini-2.5-flash-image"
        print(f"📦 Using model: {model_name}")

        # Create model
        model = genai.GenerativeModel(model_name)
        print("✅ Model initialized")

        # Test prompt
        test_prompt = "A cute robot assistant with a friendly smile, photorealistic, 4k"
        print(f"\n🖼️  Test prompt: '{test_prompt}'")

        # Generate
        print("\n⏳ Generating image... (this may take 10-30 seconds)")
        response = model.generate_content(test_prompt)

        print("✅ Response received")
        print(f"   Candidates: {len(response.candidates)}")

        if not response.candidates or len(response.candidates) == 0:
            print("❌ No candidates in response")
            return False

        candidate = response.candidates[0]
        print(f"   Parts in candidate: {len(candidate.content.parts)}")

        # Extract image
        image_data = None
        mime_type = None

        for i, part in enumerate(candidate.content.parts):
            print(f"\n   Part {i}: {type(part)}")
            if hasattr(part, "inline_data"):
                print("      ✓ Found inline_data")
                image_data = part.inline_data.data
                mime_type = part.inline_data.mime_type
                print(f"      MIME type: {mime_type}")
                print(f"      Data size: {len(image_data)} bytes")
                break
            elif hasattr(part, "text"):
                print(f"      Text part: {part.text[:100]}...")

        if not image_data:
            print("\n❌ No image data found in response")
            return False

        # Save image
        output_path = Path(__file__).parent / "test_output_nanobana.png"
        if isinstance(image_data, str):
            # If it's base64 string
            image_bytes = base64.b64decode(image_data)
        else:
            # If it's already bytes
            image_bytes = image_data

        output_path.write_bytes(image_bytes)

        print("\n✅ SUCCESS! Image generated and saved")
        print(f"   📁 Location: {output_path}")
        print(f"   📊 Size: {len(image_bytes):,} bytes")
        print(f"   🎨 MIME: {mime_type}")

        return True

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback

        print("\nFull traceback:")
        traceback.print_exc()
        return False


async def main():
    """Run test."""
    print("\n" + "🚀 THESIS IMAGE GENERATION TEST (STANDALONE) " + "\n")

    success = await test_image_generation()

    print("\n" + "=" * 70)
    print("📊 RESULT")
    print("=" * 70)
    if success:
        print("✅ Image generation PASSED")
        print("\nYou now have more credits and can generate images!")
    else:
        print("❌ Image generation FAILED")
        print("\nPlease check:")
        print("  1. GOOGLE_GENERATIVE_AI_API_KEY is set correctly")
        print("  2. API key has credits available")
        print("  3. gemini-2.5-flash-image model is accessible")
    print()


if __name__ == "__main__":
    asyncio.run(main())
