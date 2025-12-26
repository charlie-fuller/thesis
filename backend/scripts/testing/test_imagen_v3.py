"""
Test with explicit image generation request using generation_config.
"""
import asyncio
import base64
import os
from pathlib import Path

import google.generativeai as genai


async def test_with_config():
    """Test with generation config specifying image output."""
    print("🎨 Testing Gemini Image Generation with Config")
    print("=" * 70)

    # Load env
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip().strip('"').strip("'")

    api_key = os.getenv("GOOGLE_GENERATIVE_AI_API_KEY")
    if not api_key:
        print("❌ No API key")
        return False

    print(f"✅ API Key: {api_key[:15]}...{api_key[-5:]}\n")

    try:
        genai.configure(api_key=api_key)

        # Try different approaches
        test_cases = [
            {
                "name": "Experimental Image Generation Model",
                "model": "gemini-2.0-flash-exp-image-generation",
                "prompt": "Generate an image: A cute robot assistant named Thesis",
                "config": None
            },
            {
                "name": "With explicit image request",
                "model": "gemini-2.0-flash-exp-image-generation",
                "prompt": "[IMAGE] A cute robot assistant named Thesis with a friendly smile",
                "config": None
            },
            {
                "name": "Standard model with image input",
                "model": "gemini-2.0-flash",
                "prompt": "Create a detailed image of a cute robot assistant",
                "config": None
            }
        ]

        for i, test in enumerate(test_cases):
            print(f"\n{'='*70}")
            print(f"Test {i+1}: {test['name']}")
            print(f"{'='*70}")
            print(f"Model: {test['model']}")
            print(f"Prompt: {test['prompt']}")

            try:
                model = genai.GenerativeModel(test['model'])

                if test['config']:
                    response = model.generate_content(
                        test['prompt'],
                        generation_config=test['config']
                    )
                else:
                    response = model.generate_content(test['prompt'])

                print("\n✓ Response received")

                # Check for image data
                found_image = False
                if response.candidates:
                    for candidate in response.candidates:
                        for part in candidate.content.parts:
                            if hasattr(part, 'inline_data') and part.inline_data:
                                if hasattr(part.inline_data, 'data') and part.inline_data.data:
                                    found_image = True
                                    image_data = part.inline_data.data
                                    print(f"✅ FOUND IMAGE DATA! ({len(image_data)} bytes)")

                                    # Save it
                                    output_path = Path(__file__).parent / f"test_{i+1}_image.png"
                                    if isinstance(image_data, str):
                                        image_bytes = base64.b64decode(image_data)
                                    else:
                                        image_bytes = image_data
                                    output_path.write_bytes(image_bytes)
                                    print(f"💾 Saved to: {output_path}")
                                    return True

                if not found_image:
                    # Show what we got instead
                    if response.candidates and response.candidates[0].content.parts:
                        first_part = response.candidates[0].content.parts[0]
                        if hasattr(first_part, 'text'):
                            print(f"❌ Got text instead: {first_part.text[:100]}...")

            except Exception as e:
                print(f"❌ Error: {str(e)}")

        print("\n" + "="*70)
        print("🔍 Summary: No image data found in any test")
        print("="*70)

        # Additional investigation
        print("\n💡 Checking if model requires special prompt format...")
        print("\nNote: Google's Gemini models may:")
        print("  1. Require specific API access for image generation")
        print("  2. Need to use Imagen 3 API directly (not Gemini API)")
        print("  3. Be in beta/experimental phase")

        return False

    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    print("\n🚀 THESIS IMAGE GENERATION INVESTIGATION\n")
    success = await test_with_config()

    if not success:
        print("\n" + "="*70)
        print("📝 RECOMMENDATION")
        print("="*70)
        print("Gemini API may not support direct image generation yet.")
        print("You may need to:")
        print("  1. Use Vertex AI Imagen 3 API instead")
        print("  2. Check Google AI Studio for latest image gen models")
        print("  3. Apply for Imagen 3 access separately")
        print()


if __name__ == "__main__":
    asyncio.run(main())
