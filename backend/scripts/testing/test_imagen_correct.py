"""Test image generation with the correct Gemini model."""

import asyncio
import base64
import os
from pathlib import Path

import google.generativeai as genai


async def test_image_generation():
    """Test with gemini-2.0-flash-exp-image-generation."""
    print("🎨 Testing Google Gemini Image Generation")
    print("=" * 70)

    # Load .env
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip().strip('"').strip("'")

    api_key = os.getenv("GOOGLE_GENERATIVE_AI_API_KEY")
    if not api_key:
        print("❌ ERROR: GOOGLE_GENERATIVE_AI_API_KEY not set")
        return False

    print(f"✅ API Key found: {api_key[:15]}...{api_key[-5:]}\n")

    try:
        genai.configure(api_key=api_key)

        # Use the correct image generation model
        model_name = "gemini-2.0-flash-exp-image-generation"
        print(f"📦 Model: {model_name}")

        model = genai.GenerativeModel(model_name)
        print("✅ Model initialized\n")

        # Simple test prompt
        test_prompt = "A cute robot assistant named Thesis with a friendly smile"
        print(f"🖼️  Prompt: '{test_prompt}'")
        print("\n⏳ Generating image... (this may take 10-30 seconds)")

        response = model.generate_content(test_prompt)

        print("\n✅ Response received")
        print(f"   Candidates: {len(response.candidates)}")

        if not response.candidates:
            print("❌ No candidates in response")
            print(f"Response: {response}")
            return False

        candidate = response.candidates[0]
        print(f"   Parts: {len(candidate.content.parts)}")

        # Look for image data
        image_data = None
        mime_type = None

        for i, part in enumerate(candidate.content.parts):
            print(f"\n   Checking Part {i}:")

            # Check various possible attributes
            if hasattr(part, "inline_data") and part.inline_data:
                print("      ✓ Has inline_data")
                if hasattr(part.inline_data, "data"):
                    image_data = part.inline_data.data
                    mime_type = getattr(part.inline_data, "mime_type", "image/png")
                    print(f"      Data length: {len(image_data) if image_data else 0} bytes")
                    print(f"      MIME: {mime_type}")
                    break

            if hasattr(part, "text"):
                text = part.text[:200] if part.text else ""
                print(f"      Text: {text}...")

            if hasattr(part, "function_call"):
                print(f"      Function call: {part.function_call}")

        if not image_data:
            print("\n❌ No image data found in response")
            print("\nFull response structure:")
            print(response)
            return False

        # Save the image
        output_path = Path(__file__).parent / "thesis_generated_image.png"

        if isinstance(image_data, str):
            image_bytes = base64.b64decode(image_data)
        else:
            image_bytes = image_data

        output_path.write_bytes(image_bytes)

        print("\n✅ SUCCESS! Image generated")
        print(f"   📁 Saved to: {output_path}")
        print(f"   📊 Size: {len(image_bytes):,} bytes")
        print(f"   🎨 Type: {mime_type}")

        return True

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    print("\n🚀 THESIS IMAGE GENERATION TEST\n")

    success = await test_image_generation()

    print("\n" + "=" * 70)
    print("📊 RESULT")
    print("=" * 70)

    if success:
        print("✅ Image generation WORKING!")
        print("\n🎉 You have credits and can generate images with Gemini!")
    else:
        print("❌ Image generation FAILED")
        print("\nPossible issues:")
        print("  • API quota/credits exhausted")
        print("  • Model not enabled for this API key")
        print("  • API endpoint changed")
    print()


if __name__ == "__main__":
    asyncio.run(main())
