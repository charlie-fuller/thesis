"""Conversation Service.

Handles conversation context analysis, including image generation suggestions.
"""

import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Import the new L&D-specific detector
try:
    from services.image_opportunity_detector import get_image_opportunity_detector

    LD_DETECTOR_AVAILABLE = True
except ImportError:
    logger.warning("L&D Image Opportunity Detector not available")
    LD_DETECTOR_AVAILABLE = False


class ConversationService:
    """Service for analyzing conversation context and suggesting actions."""

    # Keywords that suggest visual content would be helpful
    VISUAL_KEYWORDS = [
        "visualize",
        "diagram",
        "chart",
        "graph",
        "show me",
        "what does",
        "how does",
        "illustrate",
        "picture",
        "image",
        "sketch",
        "draw",
        "layout",
        "design",
        "architecture",
        "structure",
        "flow",
        "process",
    ]

    # Educational/complex topics that benefit from visuals
    EDUCATIONAL_TOPICS = [
        "photosynthesis",
        "solar system",
        "anatomy",
        "chemistry",
        "physics",
        "biology",
        "mathematics",
        "algorithm",
        "data structure",
        "network",
        "circuit",
        "ecosystem",
        "cycle",
        "timeline",
        "hierarchy",
        "workflow",
        "architecture",
        "model",
        "framework",
        "system design",
    ]

    # Visual types that should trigger image generation
    VISUAL_TYPES = [
        "image",
        "picture",
        "drawing",
        "illustration",
        "mind map",
        "mindmap",
        "flowchart",
        "flow chart",
        "diagram",
        "infographic",
        "timeline",
        "chart",
        "visualization",
        "visual",
        "graphic",
        "schematic",
    ]

    # Explicit image request patterns
    IMAGE_REQUEST_PATTERNS = [
        r"generate (?:an? )?image (?:of )?(.+)",
        r"create (?:an? )?(?:picture|image|drawing) (?:of )?(.+)",
        r"show me (?:an? )?(?:picture|image|visual) (?:of )?(.+)",
        r"draw (.+)",
        r"make (?:an? )?(?:picture|image) (?:of )?(.+)",
        r"(?:can you |could you )?(?:generate|create|make|draw) (?:an? )?(?:image|picture) (.+)",
        # Visual types like mind map, flowchart, diagram, etc.
        r"create (?:an? )?(?:mind ?map|flowchart|flow chart|diagram|infographic|timeline|chart|visualization|schematic) (?:of |for |about |showing |exploring )?(.+)",
        r"(?:can you |could you )?(?:generate|create|make|draw) (?:an? )?(?:mind ?map|flowchart|flow chart|diagram|infographic|timeline|chart|visualization|schematic) (?:of |for |about |showing |exploring )?(.+)",
        r"(?:generate|make) (?:an? )?(?:mind ?map|flowchart|flow chart|diagram|infographic|timeline|chart|visualization|schematic) (?:of |for |about |showing |exploring )?(.+)",
    ]

    # Aspect ratio keywords
    ASPECT_RATIO_KEYWORDS = {
        "1:1": ["square", "1:1", "instagram"],
        "16:9": ["16:9", "landscape", "widescreen", "presentation", "wide"],
        "9:16": ["9:16", "portrait", "vertical", "mobile", "story"],
        "4:3": ["4:3", "standard", "classic"],
    }

    def should_suggest_image(
        self, user_message: str, assistant_response: str, recent_messages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Determine if an image suggestion should be made.

        Uses the L&D-specific Image Opportunity Detector for enhanced
        learning and development context awareness.

        Args:
            user_message: The user's latest message
            assistant_response: The assistant's response
            recent_messages: Last 5 messages for context (including metadata)

        Returns:
            Dict with:
                - suggest (bool): Whether to suggest
                - reason (str): Why suggest
                - suggested_prompt (str): Suggested image prompt
                - image_type (str): L&D image type (flowchart, diagram, etc.)
                - subject (str): Detected subject for the visual
        """
        try:
            # Try using the L&D-specific detector first
            if LD_DETECTOR_AVAILABLE:
                detector = get_image_opportunity_detector()
                result = detector.detect_opportunity(
                    user_message=user_message,
                    assistant_response=assistant_response,
                    recent_messages=recent_messages,
                )

                if result.get("suggest"):
                    # Generate the suggested prompt using the detector
                    suggested_prompt = detector.get_suggested_prompt(
                        image_type=result["image_type"], subject=result["subject"]
                    )

                    logger.info(
                        f"L&D image suggestion: {result['image_type']} "
                        f"for '{result['subject'][:50]}...'"
                    )

                    return {
                        "suggest": True,
                        "reason": result["reason"],
                        "suggested_prompt": suggested_prompt,
                        "image_type": result["image_type"],
                        "subject": result["subject"],
                    }

            # Fallback to original logic if detector not available or didn't trigger
            # Check if we've suggested recently (avoid spam)
            recent_suggestion_count = sum(
                1
                for msg in recent_messages
                if msg.get("metadata", {}).get("image_suggestion") is not None
            )

            # Max 1 suggestion per 5 messages
            if recent_suggestion_count > 0:
                logger.debug("Image suggestion throttled - suggested recently")
                return {"suggest": False}

            # Convert to lowercase for matching
            user_lower = user_message.lower()
            response_lower = assistant_response.lower()

            # Check for visual keywords
            has_visual_keyword = any(
                keyword in user_lower or keyword in response_lower
                for keyword in self.VISUAL_KEYWORDS
            )

            # Check for educational topics
            has_educational_topic = any(
                topic in user_lower or topic in response_lower for topic in self.EDUCATIONAL_TOPICS
            )

            # Check message length - complex explanations benefit from visuals
            is_complex_response = len(assistant_response.split()) > 100

            if has_visual_keyword or (has_educational_topic and is_complex_response):
                # Extract subject for suggestion
                suggested_prompt = self._extract_subject_for_image(user_message, assistant_response)

                logger.info("Image suggestion triggered (fallback logic)")
                return {
                    "suggest": True,
                    "reason": "This concept would be clearer with a visual",
                    "suggested_prompt": suggested_prompt,
                }

            return {"suggest": False}

        except Exception as e:
            logger.error(f"Error in should_suggest_image: {e}")
            return {"suggest": False}

    def extract_image_request(self, user_message: str) -> Dict[str, Any]:
        """Detect and extract explicit image generation requests.

        Uses a two-tier approach:
        1. First tries strict regex patterns for clear requests
        2. Falls back to flexible keyword detection for less structured requests

        Args:
            user_message: The user's message

        Returns:
            Dict with:
                - is_request (bool): Whether this is an image request
                - prompt (str): Extracted image prompt
                - aspect_ratio (str or None): Detected aspect ratio
                - model (str or None): Detected model preference
        """
        try:
            user_lower = user_message.lower()

            # First, try strict regex patterns
            for pattern in self.IMAGE_REQUEST_PATTERNS:
                match = re.search(pattern, user_lower, re.IGNORECASE)
                if match:
                    # Extract the prompt (everything after the command)
                    prompt = match.group(1).strip()

                    # Remove aspect ratio and model keywords from prompt
                    cleaned_prompt = self._clean_prompt(prompt)

                    # Detect aspect ratio
                    aspect_ratio = self._extract_aspect_ratio(user_message)

                    # Detect model preference
                    model = self._extract_model_preference(user_message)

                    logger.info(f"Image request detected (regex): {cleaned_prompt[:50]}...")

                    return {
                        "is_request": True,
                        "prompt": cleaned_prompt,
                        "aspect_ratio": aspect_ratio,
                        "model": model,
                    }

            # Second, try flexible keyword-based detection
            # This catches typos and non-standard phrasings
            result = self._flexible_image_detection(user_message, user_lower)
            if result.get("is_request"):
                return result

            return {"is_request": False}

        except Exception as e:
            logger.error(f"Error in extract_image_request: {e}")
            return {"is_request": False}

    def _flexible_image_detection(self, user_message: str, user_lower: str) -> Dict[str, Any]:
        """Flexible keyword-based image request detection.

        Catches requests that don't match strict regex patterns, including:
        - Typos (e.g., "dioagram", "diagramm")
        - Non-standard phrasings (e.g., "I need a visual of...")
        - Requests with colons (e.g., "create a diagram of this:")

        Args:
            user_message: Original user message
            user_lower: Lowercase version of user message

        Returns:
            Dict with is_request, prompt, aspect_ratio, model
        """
        # Visual type keywords (with common typos)
        visual_keywords = [
            "image",
            "picture",
            "diagram",
            "dioagram",
            "diagramm",
            "mind map",
            "mindmap",
            "mind-map",
            "flowchart",
            "flow chart",
            "flow-chart",
            "infographic",
            "info graphic",
            "info-graphic",
            "visualization",
            "visualisation",
            "visual",
            "chart",
            "graph",
            "graphic",
            "schematic",
            "timeline",
            "time line",
            "time-line",
            "illustration",
            "drawing",
            "sketch",
        ]

        # Action keywords that indicate generation request
        action_keywords = [
            "create",
            "generate",
            "make",
            "draw",
            "build",
            "show",
            "produce",
            "design",
            "render",
            "give me",
            "i need",
            "i want",
            "can you make",
            "please create",
            "please generate",
            "please make",
        ]

        # Check for visual keyword presence
        found_visual = None
        for visual in visual_keywords:
            if visual in user_lower:
                found_visual = visual
                break

        if not found_visual:
            return {"is_request": False}

        # Check for action keyword presence
        has_action = any(action in user_lower for action in action_keywords)

        if not has_action:
            return {"is_request": False}

        # This is an image request - extract the prompt
        # Use the full message as the prompt, we'll let Gemini figure out the content
        prompt = user_message

        # Try to extract just the subject part after common patterns
        extraction_patterns = [
            r"(?:create|generate|make|draw|build|show|produce|design|render)\s+(?:a|an|the)?\s*(?:"
            + "|".join(re.escape(v) for v in visual_keywords)
            + r")\s*(?:of|for|about|showing|exploring|on)?\s*[:\-]?\s*(.+)",
            r"(?:give me|i need|i want)\s+(?:a|an|the)?\s*(?:"
            + "|".join(re.escape(v) for v in visual_keywords)
            + r")\s*(?:of|for|about|showing|exploring|on)?\s*[:\-]?\s*(.+)",
        ]

        for pattern in extraction_patterns:
            match = re.search(pattern, user_lower, re.IGNORECASE | re.DOTALL)
            if match:
                prompt = match.group(1).strip()
                # If the extracted prompt is very short, use the full message
                if len(prompt) < 10:
                    prompt = user_message
                break

        # Clean up the prompt
        cleaned_prompt = self._clean_prompt(prompt)

        # Detect aspect ratio and model
        aspect_ratio = self._extract_aspect_ratio(user_message)
        model = self._extract_model_preference(user_message)

        logger.info(
            f"Image request detected (flexible): visual='{found_visual}', prompt='{cleaned_prompt[:50]}...'"
        )

        return {
            "is_request": True,
            "prompt": cleaned_prompt,
            "aspect_ratio": aspect_ratio,
            "model": model,
            "detected_visual_type": found_visual,
        }

    def _extract_subject_for_image(self, user_message: str, assistant_response: str) -> str:
        """Extract a good subject for image generation from context.

        Args:
            user_message: User's message
            assistant_response: Assistant's response

        Returns:
            Suggested image prompt
        """
        # Simple extraction: use the user's question or first sentence
        user_lower = user_message.lower()

        # Remove common question words
        subject = user_message
        for phrase in ["how does", "what is", "explain", "tell me about", "show me"]:
            if user_lower.startswith(phrase):
                subject = user_message[len(phrase) :].strip()
                break

        # Limit length
        words = subject.split()
        if len(words) > 10:
            subject = " ".join(words[:10])

        return f"diagram showing {subject}"

    def _extract_aspect_ratio(self, text: str) -> Optional[str]:
        """Extract aspect ratio from text.

        Args:
            text: Message text

        Returns:
            Aspect ratio string or None
        """
        text_lower = text.lower()

        for ratio, keywords in self.ASPECT_RATIO_KEYWORDS.items():
            if any(keyword in text_lower for keyword in keywords):
                return ratio

        return None

    def _extract_model_preference(self, text: str) -> Optional[str]:
        """Extract model preference from text.

        Args:
            text: Message text

        Returns:
            Model key ('fast' or 'quality') or None
        """
        text_lower = text.lower()

        if any(word in text_lower for word in ["fast", "quick", "rapid", "speed"]):
            return "fast"
        elif any(word in text_lower for word in ["quality", "high quality", "detailed", "best"]):
            return "quality"

        return None

    def _clean_prompt(self, prompt: str) -> str:
        """Remove aspect ratio and model keywords from prompt.

        Args:
            prompt: Raw prompt text

        Returns:
            Cleaned prompt
        """
        # Remove aspect ratio mentions
        for keywords in self.ASPECT_RATIO_KEYWORDS.values():
            for keyword in keywords:
                prompt = re.sub(rf"\b{keyword}\b", "", prompt, flags=re.IGNORECASE)

        # Remove model preference words
        for word in ["fast", "quick", "quality", "high quality", "detailed"]:
            prompt = re.sub(rf"\b{word}\b", "", prompt, flags=re.IGNORECASE)

        # Remove "in" at the beginning (e.g., "in 16:9" -> "")
        prompt = re.sub(r"^\s*in\s+", "", prompt, flags=re.IGNORECASE)

        # Clean up extra whitespace
        prompt = " ".join(prompt.split())

        return prompt.strip()


# Global singleton
_conversation_service: Optional[ConversationService] = None


def get_conversation_service() -> ConversationService:
    """Get or create the global ConversationService instance."""
    global _conversation_service
    if _conversation_service is None:
        _conversation_service = ConversationService()
    return _conversation_service
