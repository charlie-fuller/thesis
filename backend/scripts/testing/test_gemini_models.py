"""
Check what Gemini models are available and test image generation.
"""
import os
from pathlib import Path

import google.generativeai as genai


def load_env():
    """Load environment variables."""
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip().strip('"').strip("'")


def main():
    """List available models."""
    print("🔍 Checking Available Google Generative AI Models")
    print("=" * 70)

    load_env()

    api_key = os.getenv("GOOGLE_GENERATIVE_AI_API_KEY")
    if not api_key:
        print("❌ GOOGLE_GENERATIVE_AI_API_KEY not set")
        return

    print(f"✅ API Key: {api_key[:15]}...{api_key[-5:]}\n")

    try:
        genai.configure(api_key=api_key)

        print("📋 Available Models:\n")

        for model in genai.list_models():
            print(f"Model: {model.name}")
            print(f"  Display Name: {model.display_name}")
            print(f"  Description: {model.description[:100]}...")

            # Check capabilities
            supported_methods = []
            if hasattr(model, 'supported_generation_methods'):
                supported_methods = model.supported_generation_methods

            print(f"  Supported methods: {supported_methods}")

            # Check if it supports image generation
            if 'generateContent' in supported_methods:
                print("  ✓ Supports generateContent")

            print()

        # Check specifically for image generation models
        print("\n🎨 Searching for Image Generation Models:\n")

        image_keywords = ['image', 'imagen', 'vision', 'picture', 'photo']

        for model in genai.list_models():
            model_lower = model.name.lower()
            if any(keyword in model_lower for keyword in image_keywords):
                print(f"✓ Found: {model.name}")
                print(f"  Display: {model.display_name}")
                print(f"  Methods: {model.supported_generation_methods}")
                print()

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
