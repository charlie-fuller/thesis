"""
Image Opportunity Detector Service
Detects when visual content would enhance L&D conversations
"""

import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ImageOpportunityDetector:
    """
    Detects opportunities for generating L&D-specific visuals in conversations.

    This service analyzes conversation context to determine when images would
    enhance learning and development discussions, and suggests appropriate
    visual types (flowcharts, diagrams, infographics, etc.).
    """

    # L&D-specific trigger patterns
    LD_TRIGGERS = {
        'flowchart': {
            'keywords': [
                'process', 'steps', 'workflow', 'procedure', 'how to',
                'sequence', 'flow', 'stage', 'phase', 'methodology'
            ],
            'reason': 'A flowchart would help visualize this process'
        },
        'diagram': {
            'keywords': [
                'concept', 'model', 'framework', 'theory', 'structure',
                'architecture', 'system', 'relationship', 'connection', 'hierarchy'
            ],
            'reason': 'A concept diagram would clarify these relationships'
        },
        'infographic': {
            'keywords': [
                'data', 'statistics', 'numbers', 'metrics', 'percentage',
                'findings', 'results', 'survey', 'study', 'research'
            ],
            'reason': 'An infographic would make this data more engaging'
        },
        'timeline': {
            'keywords': [
                'timeline', 'history', 'evolution', 'chronological', 'sequence',
                'development', 'progression', 'milestone', 'events', 'period'
            ],
            'reason': 'A timeline would show this progression clearly'
        },
        'comparison': {
            'keywords': [
                'compare', 'comparison', 'versus', 'vs', 'difference', 'contrast',
                'alternative', 'option', 'choice', 'pros and cons', 'advantages'
            ],
            'reason': 'A comparison chart would highlight the differences'
        },
        'mindmap': {
            'keywords': [
                'brainstorm', 'ideas', 'concepts', 'categories', 'topics',
                'mind map', 'branches', 'explore', 'ideation', 'organize'
            ],
            'reason': 'A mind map would help organize these ideas'
        }
    }

    # Complex learning topics that benefit from visuals
    COMPLEX_TOPICS = [
        # Business & Leadership
        'agile', 'scrum', 'lean', 'six sigma', 'kanban', 'okr',
        'swot', 'pestle', 'business model', 'value proposition',
        'customer journey', 'stakeholder', 'organizational',

        # Technical & IT
        'architecture', 'deployment', 'infrastructure', 'network',
        'database', 'api', 'microservices', 'cloud', 'devops',

        # Educational & Training
        'learning path', 'curriculum', 'competency', 'skill gap',
        'training program', 'onboarding', 'development plan',
        'instructional design', 'bloom taxonomy', 'assessment',

        # Science & Analysis
        'cycle', 'ecosystem', 'taxonomy', 'classification',
        'analysis', 'methodology', 'framework', 'matrix'
    ]

    # Patterns that suggest multiple steps
    MULTI_STEP_PATTERNS = [
        r'\d+\.\s',  # Numbered lists: "1. ", "2. "
        r'first[,\s].*second',  # "first... second..."
        r'step \d+',  # "step 1", "step 2"
        r'stage \d+',  # "stage 1", "stage 2"
    ]

    def detect_opportunity(
        self,
        user_message: str,
        assistant_response: str,
        recent_messages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Detect if an image would enhance the conversation.

        Args:
            user_message: User's latest message
            assistant_response: Assistant's response
            recent_messages: Recent conversation context

        Returns:
            Dict with:
                - suggest (bool): Whether to suggest an image
                - image_type (str): Suggested L&D image type
                - subject (str): Detected subject for the visual
                - reason (str): Why this visual would help
                - confidence (float): Confidence score 0-1
        """
        try:
            # Check if we've suggested recently (throttle)
            recent_suggestion_count = sum(
                1 for msg in recent_messages
                if msg.get('metadata', {}).get('image_suggestion') is not None
            )

            # Max 1 suggestion per 5 messages
            if recent_suggestion_count > 0:
                logger.debug("Image suggestion throttled - suggested recently")
                return {"suggest": False}

            # Combine messages for analysis
            combined_text = f"{user_message} {assistant_response}".lower()

            # Detect image type based on keywords
            detected_types = self._detect_image_types(combined_text)

            if not detected_types:
                return {"suggest": False}

            # Get the highest scoring type
            best_type = max(detected_types.items(), key=lambda x: x[1])
            image_type, score = best_type

            # Extract subject
            subject = self._extract_subject(user_message, assistant_response)

            # Check for additional signals
            has_complex_topic = self._has_complex_topic(combined_text)
            has_multi_steps = self._has_multi_steps(assistant_response)
            is_long_explanation = len(assistant_response.split()) > 80

            # Calculate confidence
            confidence = score
            if has_complex_topic:
                confidence += 0.15
            if has_multi_steps:
                confidence += 0.1
            if is_long_explanation:
                confidence += 0.05

            confidence = min(confidence, 1.0)

            # Only suggest if confidence is high enough
            if confidence >= 0.35:
                logger.info(
                    f"Image opportunity detected: {image_type} for '{subject[:50]}...' "
                    f"(confidence: {confidence:.2f})"
                )

                return {
                    "suggest": True,
                    "image_type": image_type,
                    "subject": subject,
                    "reason": self.LD_TRIGGERS[image_type]['reason'],
                    "confidence": confidence
                }

            return {"suggest": False}

        except Exception as e:
            logger.error(f"Error in detect_opportunity: {e}", exc_info=True)
            return {"suggest": False}

    def _detect_image_types(self, text: str) -> Dict[str, float]:
        """
        Detect which image types are relevant based on text.

        Args:
            text: Text to analyze

        Returns:
            Dict mapping image type to confidence score
        """
        detected = {}

        for image_type, config in self.LD_TRIGGERS.items():
            keywords = config['keywords']
            matches = sum(1 for keyword in keywords if keyword in text)

            if matches > 0:
                # Score based on number of matching keywords
                score = min(0.3 + (matches * 0.1), 0.8)
                detected[image_type] = score

        return detected

    def _has_complex_topic(self, text: str) -> bool:
        """Check if text contains complex L&D topics"""
        return any(topic in text for topic in self.COMPLEX_TOPICS)

    def _has_multi_steps(self, text: str) -> bool:
        """Check if text contains multiple steps/stages"""
        return any(re.search(pattern, text) for pattern in self.MULTI_STEP_PATTERNS)

    def _extract_subject(self, user_message: str, assistant_response: str) -> str:
        """
        Extract the main subject for image generation.

        Args:
            user_message: User's message
            assistant_response: Assistant's response

        Returns:
            Subject string for image prompt
        """
        # Try to extract from user's question
        user_lower = user_message.lower()

        # Remove common question prefixes
        subject = user_message
        for prefix in [
            'how does ', 'what is ', 'what are ', 'explain ', 'tell me about ',
            'show me ', 'can you explain ', 'help me understand ', 'describe '
        ]:
            if user_lower.startswith(prefix):
                subject = user_message[len(prefix):].strip()
                break

        # Clean up question marks and extra words
        subject = subject.rstrip('?')

        # Limit length
        words = subject.split()
        if len(words) > 12:
            subject = ' '.join(words[:12])

        # If subject is too short, try to extract from first sentence
        if len(subject.split()) < 3:
            sentences = assistant_response.split('.')
            if sentences:
                first_sentence = sentences[0].strip()
                words = first_sentence.split()
                if len(words) > 3:
                    subject = ' '.join(words[:10])

        return subject

    def get_suggested_prompt(
        self,
        image_type: str,
        subject: str
    ) -> str:
        """
        Generate a suggested prompt for the image type.

        Args:
            image_type: Type of image (flowchart, diagram, etc.)
            subject: Subject matter

        Returns:
            Suggested prompt string
        """
        templates = {
            'flowchart': f'A detailed flowchart showing the process of {subject}, with clear steps, decision points, and flow arrows',
            'diagram': f'An educational diagram illustrating {subject}, showing key concepts and their relationships',
            'infographic': f'A clean, professional infographic about {subject}, displaying key statistics and data points visually',
            'timeline': f'A timeline visualization showing {subject}, with clear chronological progression and key milestones',
            'comparison': f'A comparison chart contrasting {subject}, highlighting key differences and similarities in a clear visual format',
            'mindmap': f'A mind map exploring {subject}, with central concept and branching related ideas and connections'
        }

        return templates.get(image_type, f'A visual representation of {subject}')


# Global singleton
_detector_instance: Optional[ImageOpportunityDetector] = None


def get_image_opportunity_detector() -> ImageOpportunityDetector:
    """Get or create the global ImageOpportunityDetector instance"""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = ImageOpportunityDetector()
    return _detector_instance
