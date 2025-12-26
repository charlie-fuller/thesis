"""
Test Google Gemini image generation using direct HTTP REST calls.
Based on official Google AI documentation.
"""
import base64
import json
import os
from pathlib import Path

import requests


def load_env():
    """Load environment variables from .env file."""
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip().strip('"').strip("'")


def test_gemini_image_http():
    """Test image generation using direct HTTP REST API."""
    print("🎨 Testing Gemini Image Generation via HTTP REST API")
    print("=" * 70)

    load_env()

    api_key = os.getenv("GOOGLE_GENERATIVE_AI_API_KEY")
    if not api_key:
        print("❌ ERROR: GOOGLE_GENERATIVE_AI_API_KEY not set")
        return False

    print(f"✅ API Key: {api_key[:15]}...{api_key[-5:]}\n")

    # Test 1: Gemini 2.5 Flash Image (nano banana)
    print("Test 1: gemini-2.5-flash-image (nano banana)")
    print("-" * 70)

    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent"

    headers = {
        "x-goog-api-key": api_key,
        "Content-Type": "application/json"
    }

    prompt = "A friendly robot assistant with a smile, digital art style"

    payload = {
        "contents": [{
            "parts": [
                {"text": prompt}
            ]
        }]
    }

    print(f"📝 Prompt: {prompt}")
    print(f"🔗 URL: {url}")
    print("\n⏳ Sending request...")

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)

        print(f"📊 Status Code: {response.status_code}")

        if response.status_code != 200:
            print(f"❌ Error Response: {response.text[:500]}")
            return False

        data = response.json()

        # Check for image data
        if "candidates" in data and len(data["candidates"]) > 0:
            candidate = data["candidates"][0]

            if "content" in candidate and "parts" in candidate["content"]:
                for i, part in enumerate(candidate["content"]["parts"]):
                    print(f"\nPart {i}: {list(part.keys())}")

                    if "inlineData" in part:
                        inline_data = part["inlineData"]

                        if "data" in inline_data:
                            image_b64 = inline_data["data"]
                            mime_type = inline_data.get("mimeType", "image/png")

                            print("✅ FOUND IMAGE DATA!")
                            print(f"   MIME Type: {mime_type}")
                            print(f"   Base64 length: {len(image_b64)}")

                            # Decode and save
                            image_bytes = base64.b64decode(image_b64)
                            output_path = Path(__file__).parent / "nanobana_output.png"
                            output_path.write_bytes(image_bytes)

                            print(f"\n💾 Image saved to: {output_path}")
                            print(f"📊 File size: {len(image_bytes):,} bytes")

                            return True

                    elif "text" in part:
                        print(f"   Text: {part['text'][:100]}...")

        print("\n❌ No image data found in response")
        print(f"\nFull response structure: {json.dumps(data, indent=2)[:500]}...")
        return False

    except requests.exceptions.Timeout:
        print("❌ Request timed out (60s)")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_imagen_endpoint():
    """Test with Imagen 4.0 endpoint."""
    print("\n" + "=" * 70)
    print("Test 2: imagen-4.0-generate-001")
    print("-" * 70)

    api_key = os.getenv("GOOGLE_GENERATIVE_AI_API_KEY")

    url = "https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict"

    headers = {
        "x-goog-api-key": api_key,
        "Content-Type": "application/json"
    }

    prompt = "A friendly robot assistant with a smile, digital art style"

    payload = {
        "instances": [{
            "prompt": prompt
        }],
        "parameters": {
            "sampleCount": 1
        }
    }

    print(f"📝 Prompt: {prompt}")
    print(f"🔗 URL: {url}")
    print("\n⏳ Sending request...")

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)

        print(f"📊 Status Code: {response.status_code}")

        if response.status_code != 200:
            print(f"❌ Error Response: {response.text[:500]}")
            return False

        data = response.json()

        # Check for predictions
        if "predictions" in data and len(data["predictions"]) > 0:
            for i, prediction in enumerate(data["predictions"]):
                if "bytesBase64Encoded" in prediction:
                    image_b64 = prediction["bytesBase64Encoded"]

                    print(f"✅ FOUND IMAGE DATA in prediction {i}!")
                    print(f"   Base64 length: {len(image_b64)}")

                    # Decode and save
                    image_bytes = base64.b64decode(image_b64)
                    output_path = Path(__file__).parent / "imagen_output.png"
                    output_path.write_bytes(image_bytes)

                    print(f"\n💾 Image saved to: {output_path}")
                    print(f"📊 File size: {len(image_bytes):,} bytes")

                    return True

        print("\n❌ No image data found in response")
        print(f"\nFull response: {json.dumps(data, indent=2)[:500]}...")
        return False

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n🚀 THESIS IMAGE GENERATION TEST - HTTP REST API\n")

    test1_success = test_gemini_image_http()

    if not test1_success:
        test2_success = test_imagen_endpoint()
    else:
        test2_success = False

    print("\n" + "=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)

    if test1_success or test2_success:
        print("✅ SUCCESS - Image generation is working!")
        print("\n🎉 You can now generate images with Google's API!")
    else:
        print("❌ Both endpoints failed")
        print("\nPossible issues:")
        print("  • API key may not have image generation enabled")
        print("  • Model may require allowlist access")
        print("  • Check API quotas in Google AI Studio")

    print()


if __name__ == "__main__":
    main()
