"""Test with generic prompts that won't trigger policy violations."""

import asyncio
import base64
import os
from pathlib import Path

import google.generativeai as genai


async def test_generic_prompts():
    """Test with safe, generic prompts."""
    print("🎨 Testing Image Generation with Generic Prompts")
    print("=" * 70)

    # Load env
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
        print("❌ No API key")
        return False

    print(f"✅ API Key: {api_key[:15]}...{api_key[-5:]}\n")

    try:
        genai.configure(api_key=api_key)

        # Test with very simple, safe prompts
        test_prompts = [
            "A red apple on a wooden table",
            "A blue butterfly on a flower",
            "A cute cartoon robot, digital art style",
            "A sunset over mountains",
            "A friendly robot character in cartoon style",
        ]

        model_name = "gemini-2.0-flash-exp-image-generation"
        print(f"Model: {model_name}\n")

        for i, prompt in enumerate(test_prompts):
            print(f"\n{'=' * 70}")
            print(f"Test {i + 1}: {prompt}")
            print("=" * 70)

            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)

                # Look for image
                found_image = False
                if response.candidates:
                    candidate = response.candidates[0]

                    # Debug: show what we got
                    print(f"Finish reason: {candidate.finish_reason}")

                    for j, part in enumerate(candidate.content.parts):
                        print(f"Part {j}: {type(part)}")

                        if hasattr(part, "inline_data") and part.inline_data:
                            print("  Has inline_data")
                            if hasattr(part.inline_data, "data"):
                                data = part.inline_data.data
                                print(f"  Data: {len(data) if data else 0} bytes")
                                if data and len(data) > 0:
                                    found_image = True
                                    print("\n✅ FOUND IMAGE DATA!")

                                    # Save
                                    output_path = Path(__file__).parent / f"generated_image_{i + 1}.png"
                                    if isinstance(data, str):
                                        image_bytes = base64.b64decode(data)
                                    else:
                                        image_bytes = data

                                    output_path.write_bytes(image_bytes)
                                    print(f"💾 Saved: {output_path}")
                                    print(f"📊 Size: {len(image_bytes):,} bytes")

                                    return True  # Success!

                        elif hasattr(part, "text"):
                            text_preview = part.text[:150]
                            print(f"  Text: {text_preview}...")

                if not found_image:
                    print("❌ No image data found")

            except Exception as e:
                print(f"❌ Error: {str(e)}")

        print("\n" + "=" * 70)
        print("📊 CONCLUSION")
        print("=" * 70)
        print("No images were generated from any prompt.")
        print("\nThis suggests:")
        print("  • Image generation may not be available with this API key")
        print("  • The model may be text-only despite the name")
        print("  • Imagen 3 requires Vertex AI instead of Gemini API")

        return False

    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    print("\n🚀 GENERIC IMAGE GENERATION TEST\n")

    success = await test_generic_prompts()

    print("\n" + "=" * 70)
    if success:
        print("✅ SUCCESS - Image generation is working!")
    else:
        print("❌ Image generation not available")
        print("\n💡 Next steps:")
        print("  1. Verify API key has Imagen 3 access enabled")
        print("  2. Check if Vertex AI credentials are needed")
        print("  3. Review Google AI Studio for image generation setup")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
