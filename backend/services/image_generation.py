"""Image generation service using Google's Gemini (Nano Banana) API.
Uses direct HTTP REST API for reliable image generation.
"""

import logging
import os
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)


class ImageGenerationService:
    """Service for generating images using Google's Gemini image models."""

    # Available models with metadata
    MODELS = {
        "fast": {
            "name": "gemini-2.5-flash-image",
            "display_name": "Fast ⚡",
            "description": "Quick generation, good quality",
            "speed": "fast",
        },
        "quality": {
            "name": "gemini-3-pro-image-preview",
            "display_name": "Quality 🎨",
            "description": "Higher quality, slower generation",
            "speed": "slow",
        },
    }

    # Aspect ratio configurations
    ASPECT_RATIOS = {
        "1:1": {"width": 1024, "height": 1024, "description": "Square"},
        "16:9": {"width": 1536, "height": 864, "description": "Landscape (presentation)"},
        "9:16": {"width": 864, "height": 1536, "description": "Portrait (mobile)"},
        "4:3": {"width": 1280, "height": 960, "description": "Standard"},
    }

    def __init__(self):
        """Initialize the image generation service."""
        api_key = os.getenv("GOOGLE_GENERATIVE_AI_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_GENERATIVE_AI_API_KEY environment variable is not set")

        self.api_key = api_key
        self.default_model = self.MODELS["fast"]["name"]
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    def _enhance_prompt_with_aspect_ratio(self, prompt: str, aspect_ratio: str) -> str:
        """Enhance the prompt with aspect ratio information.

        Args:
            prompt: Original user prompt
            aspect_ratio: Desired aspect ratio (1:1, 16:9, 9:16, 4:3)

        Returns:
            Enhanced prompt with aspect ratio guidance
        """
        if aspect_ratio not in self.ASPECT_RATIOS:
            aspect_ratio = "16:9"  # Default fallback

        ratio_info = self.ASPECT_RATIOS[aspect_ratio]
        description = ratio_info["description"]

        # Add aspect ratio guidance to prompt
        enhanced = f"Create a {aspect_ratio} {description.lower()} format image. {prompt}"
        return enhanced

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about available models."""
        return {
            "models": self.MODELS,
            "aspect_ratios": self.ASPECT_RATIOS,
            "default_model": self.default_model,
        }

    async def generate_image(
        self, prompt: str, model: Optional[str] = None, aspect_ratio: str = "16:9", **kwargs
    ) -> Dict[str, Any]:
        """Generate an image from a text prompt using HTTP REST API.

        Args:
            prompt: Text description of the image to generate
            model: Optional model name (use model key like "fast" or "quality", or full name)
            aspect_ratio: Desired aspect ratio (1:1, 16:9, 9:16, 4:3). Default: 16:9
            **kwargs: Additional generation parameters

        Returns:
            Dictionary containing:
                - image_data: Base64-encoded image string
                - mime_type: Image MIME type (e.g., 'image/png')
                - prompt: Original prompt used
                - enhanced_prompt: Prompt with aspect ratio info
                - model: Model used for generation
                - aspect_ratio: Aspect ratio used

        Raises:
            Exception: If image generation fails
        """
        try:
            # Resolve model name (support both "fast"/"quality" keys and full model names)
            if model and model in self.MODELS:
                model_name = self.MODELS[model]["name"]
                model_key = model
            elif model:
                model_name = model
                # Try to find matching key
                model_key = next((k for k, v in self.MODELS.items() if v["name"] == model), "fast")
            else:
                model_name = self.default_model
                model_key = "fast"

            # Validate aspect ratio
            if aspect_ratio not in self.ASPECT_RATIOS:
                logger.warning(f"Invalid aspect ratio '{aspect_ratio}', using 16:9")
                aspect_ratio = "16:9"

            # Enhance prompt with aspect ratio
            enhanced_prompt = self._enhance_prompt_with_aspect_ratio(prompt, aspect_ratio)

            logger.info(f"Generating image with model {model_name} ({aspect_ratio})")
            logger.debug(f"Enhanced prompt: {enhanced_prompt[:100]}...")

            # Construct API endpoint
            url = f"{self.base_url}/models/{model_name}:generateContent"

            # Prepare headers
            headers = {"x-goog-api-key": self.api_key, "Content-Type": "application/json"}

            # Prepare request payload
            payload = {"contents": [{"parts": [{"text": enhanced_prompt}]}]}

            # Make HTTP request
            response = requests.post(url, headers=headers, json=payload, timeout=60)

            if response.status_code != 200:
                error_msg = f"API returned status {response.status_code}: {response.text[:200]}"
                logger.error(error_msg)
                raise Exception(error_msg)

            data = response.json()

            # Debug: Log response structure
            logger.info(f"API Response keys: {list(data.keys())}")
            if "candidates" in data:
                logger.info(f"Number of candidates: {len(data['candidates'])}")
                if len(data["candidates"]) > 0:
                    candidate = data["candidates"][0]
                    logger.info(f"Candidate keys: {list(candidate.keys())}")
                    if "content" in candidate:
                        logger.info(f"Content keys: {list(candidate['content'].keys())}")
                        if "parts" in candidate["content"]:
                            logger.info(f"Number of parts: {len(candidate['content']['parts'])}")
                            for i, part in enumerate(candidate["content"]["parts"]):
                                logger.info(f"Part {i} keys: {list(part.keys())}")

            # Extract image data from response
            if "candidates" not in data or len(data["candidates"]) == 0:
                raise Exception("No image generated in response")

            candidate = data["candidates"][0]

            if "content" not in candidate or "parts" not in candidate["content"]:
                raise Exception("Invalid response structure")

            # Extract image from parts
            image_data = None
            mime_type = "image/png"

            for part in candidate["content"]["parts"]:
                if "inlineData" in part:
                    inline_data = part["inlineData"]
                    if "data" in inline_data:
                        image_data = inline_data["data"]
                        mime_type = inline_data.get("mimeType", "image/png")
                        logger.info(f"✅ Found image data in inlineData: {len(image_data)} chars")
                        break
                else:
                    logger.info(f"Part does not contain inlineData, has: {list(part.keys())}")

            if not image_data:
                logger.error("No image data found after checking all parts")
                raise Exception("No image data found in response")

            logger.info(f"Image generated successfully - {len(image_data)} bytes (base64)")

            return {
                "image_data": image_data,
                "mime_type": mime_type,
                "prompt": prompt,
                "enhanced_prompt": enhanced_prompt,
                "model": model_name,
                "model_key": model_key,
                "aspect_ratio": aspect_ratio,
                "success": True,
            }

        except requests.exceptions.Timeout:
            error_msg = "Request timed out after 60 seconds"
            logger.error(error_msg)
            raise Exception(error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            logger.error(f"Error generating image: {str(e)}")
            raise Exception(f"Failed to generate image: {str(e)}")

    async def generate_multiple_images(
        self, prompts: list[str], model: Optional[str] = None
    ) -> list[Dict[str, Any]]:
        """Generate multiple images from a list of prompts.

        Args:
            prompts: List of text descriptions
            model: Optional model override

        Returns:
            List of dictionaries, each containing image data
        """
        results = []
        for prompt in prompts:
            try:
                result = await self.generate_image(prompt, model)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to generate image for prompt '{prompt}': {str(e)}")
                results.append({"error": str(e), "prompt": prompt, "success": False})

        return results


# Global instance
_image_service: Optional[ImageGenerationService] = None


def get_image_generation_service() -> ImageGenerationService:
    """Get or create the global image generation service instance."""
    global _image_service
    if _image_service is None:
        _image_service = ImageGenerationService()
    return _image_service
