"""Document Classifier Service - Automatic Agent Relevance Tagging.

Classifies uploaded documents to determine which agents should have access.
Uses a hybrid approach:
1. Fast keyword scoring (free, instant)
2. LLM classification for ambiguous cases (Claude Haiku)

Auto-tags confident classifications (>80%), prompts user for ambiguous ones.
"""

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Optional

import anthropic

from database import get_supabase

logger = logging.getLogger(__name__)


@dataclass
class AgentClassification:
    """Classification result for a single agent."""

    agent_id: str
    agent_name: str
    confidence: float
    relevance_score: float
    reason: str


@dataclass
class DocumentClassificationResult:
    """Full classification result for a document."""

    document_id: str
    detected_type: str
    classifications: list[AgentClassification] = field(default_factory=list)
    requires_user_review: bool = False
    review_reason: Optional[str] = None
    classification_method: str = "keyword"  # 'keyword', 'llm', 'hybrid'
    model_used: Optional[str] = None
    tokens_used: int = 0
    processing_time_ms: int = 0


class DocumentClassifier:
    """Classifies documents for agent relevance.

    Workflow:
    1. Extract first 3 chunks of document
    2. Score against keyword patterns (fast, free)
    3. If ambiguous, use LLM classification (Claude Haiku)
    4. Return confidence scores with review flags
    """

    # Confidence thresholds
    HIGH_CONFIDENCE_THRESHOLD = 0.80  # Auto-tag without user review
    MEDIUM_CONFIDENCE_THRESHOLD = 0.60  # Auto-tag but show notification
    LOW_CONFIDENCE_THRESHOLD = 0.40  # Below this, don't tag

    # Keyword patterns for each agent (extended from AgentRouter)
    # Includes document-type-specific patterns
    AGENT_KEYWORDS = {
        "atlas": [
            # Research/Analysis patterns
            r"\bresearch\b",
            r"\bstudy\b",
            r"\bstudies\b",
            r"\bcase study\b",
            r"\bconsulting\b",
            r"\bmckinsey\b",
            r"\bbcg\b",
            r"\bbain\b",
            r"\baccenture\b",
            r"\bdeloitte\b",
            r"\bkpmg\b",
            r"\bpwc\b",
            r"\bey\b",
            r"\bgartner\b",
            r"\bforrester\b",
            r"\bidc\b",
            r"\bwhitepaper\b",
            r"\breport\b",
            r"\banalysis\b",
            r"\btrend\b",
            r"\bbest practice\b",
            r"\bindustry\b",
            r"\bcompetitor\b",
            r"\bai implementation\b",
            r"\bgenai\b",
            r"\bgen ai\b",
            r"\bbenchmark\b",
            r"\bleading practice\b",
            r"\bmarket research\b",
        ],
        "capital": [
            # Financial patterns
            r"\broi\b",
            r"\breturn on investment\b",
            r"\bcost\b",
            r"\bbudget\b",
            r"\bfinance\b",
            r"\bfinancial\b",
            r"\bcfo\b",
            r"\bcontroller\b",
            r"\bsaving\b",
            r"\bexpense\b",
            r"\binvestment\b",
            r"\bspend\b",
            r"\bjustify\b",
            r"\bjustification\b",
            r"\bbusiness case\b",
            r"\bpayback\b",
            r"\bbreakeven\b",
            r"\bvalue\b",
            r"\bprofit\b",
            # Document types
            r"\binvoice\b",
            r"\bquote\b",
            r"\bproposal\b",
            r"\bpurchase order\b",
            r"\bbalance sheet\b",
            r"\bincome statement\b",
            r"\bcash flow\b",
            r"\bprofit.?loss\b",
            r"\bp&l\b",
            r"\baudit\b",
        ],
        "guardian": [
            # Security/Compliance patterns
            r"\bsecurity\b",
            r"\bgovernance\b",
            r"\bcompliance\b",
            r"\brisk\b",
            r"\bit\b",
            r"\binfrastructure\b",
            r"\barchitecture\b",
            r"\bpolicy\b",
            r"\bpolicies\b",
            r"\bstandard\b",
            r"\bframework\b",
            r"\bdata protection\b",
            r"\bprivacy\b",
            r"\bgdpr\b",
            r"\bccpa\b",
            r"\baudit\b",
            r"\bcontrol\b",
            r"\baccess\b",
            r"\bpermission\b",
            r"\bciso\b",
            r"\bcio\b",
            r"\bsoc2\b",
            r"\biso\b",
            r"\bhipaa\b",
            # IT patterns
            r"\bnetwork\b",
            r"\bserver\b",
            r"\bfirewall\b",
            r"\bvpn\b",
            r"\bencryption\b",
            r"\bcyber\b",
            r"\bvulnerability\b",
        ],
        "counselor": [
            # Legal patterns
            r"\blegal\b",
            r"\bcontract\b",
            r"\bagreement\b",
            r"\bterms\b",
            r"\blicense\b",
            r"\blicensing\b",
            r"\bip\b",
            r"\bintellectual property\b",
            r"\bpatent\b",
            r"\bcopyright\b",
            r"\btrademark\b",
            r"\bliability\b",
            r"\bindemnity\b",
            r"\bwarranty\b",
            r"\blawyer\b",
            r"\battorney\b",
            r"\bcounsel\b",
            # Document types
            r"\bnda\b",
            r"\bmsa\b",
            r"\bsow\b",
            r"\bsla\b",
            r"\bstatement of work\b",
            r"\bmaster service\b",
            r"\bterms of service\b",
            r"\bprivacy policy\b",
        ],
        "oracle": [
            # Meeting/Transcript patterns
            r"\btranscript\b",
            r"\bmeeting\b",
            r"\bcall\b",
            r"\bconversation\b",
            r"\battendee\b",
            r"\bparticipant\b",
            r"\bspeaker\b",
            r"\bsentiment\b",
            r"\bfeedback\b",
            r"\breaction\b",
            r"\bgranola\b",
            r"\botter\b",
            r"\bzoom\b",
            r"\bteams\b",
            r"\binterview\b",
            r"\bnotes\b",
            r"\bminutes\b",
            r"\bstakeholder\b",
            r"\bdiscussion\b",
        ],
        "sage": [
            # Change management/HR patterns
            r"\bpeople\b",
            r"\bchange management\b",
            r"\badoption\b",
            r"\bresistance\b",
            r"\bfear\b",
            r"\banxiety\b",
            r"\bburnout\b",
            r"\bchampion\b",
            r"\bculture\b",
            r"\bhuman\b",
            r"\bflourishing\b",
            r"\bpsychology\b",
            r"\bsafety\b",
            r"\bmorale\b",
            r"\bengagement\b",
            r"\bemployee\b",
            r"\bteam\b",
            r"\bpeople-first\b",
            r"\bhuman-centered\b",
            # HR document types
            r"\bjob description\b",
            r"\bperformance review\b",
            r"\borganization chart\b",
            r"\bhr policy\b",
            r"\bbenefits\b",
            r"\bonboarding\b",
        ],
        "strategist": [
            # Executive/Strategy patterns
            r"\bexecutive\b",
            r"\bc-suite\b",
            r"\bceo\b",
            r"\bboard\b",
            r"\bsponsor\b",
            r"\bstakeholder management\b",
            r"\bcoalition\b",
            r"\bpolitics\b",
            r"\bgovernance structure\b",
            r"\bstrategic alignment\b",
            r"\btransformation\b",
            r"\bleadership\b",
            r"\bbuy-in\b",
            # Document types
            r"\bstrategic plan\b",
            r"\broadmap\b",
            r"\bvision\b",
            r"\bmission\b",
            r"\bboard presentation\b",
            r"\bexecutive summary\b",
        ],
        "architect": [
            # Technical architecture patterns
            r"\barchitecture\b",
            r"\bintegration\b",
            r"\bapi\b",
            r"\btechnical design\b",
            r"\bbuild vs buy\b",
            r"\brag\b",
            r"\bvector\b",
            r"\bembedding\b",
            r"\bmlops\b",
            r"\bdevops\b",
            r"\bmicroservices\b",
            r"\bdata pipeline\b",
            r"\bsystem design\b",
            r"\btechnical\b",
            # Document types
            r"\barchitecture diagram\b",
            r"\bapi documentation\b",
            r"\bsequence diagram\b",
            r"\ber diagram\b",
            r"\bdata model\b",
            r"\btechnical spec\b",
        ],
        "operator": [
            # Operations patterns
            r"\bprocess\b",
            r"\bworkflow\b",
            r"\bautomation\b",
            r"\bmetrics\b",
            r"\bkpi\b",
            r"\bbaseline\b",
            r"\bexception\b",
            r"\bsop\b",
            r"\boperations\b",
            r"\befficiency\b",
            r"\bthroughput\b",
            r"\bbottleneck\b",
            r"\bfrontline\b",
            r"\bday-to-day\b",
            # Document types
            r"\bstandard operating procedure\b",
            r"\bprocess map\b",
            r"\bworkflow diagram\b",
            r"\brunbook\b",
            r"\bplaybook\b",
        ],
        "pioneer": [
            # Innovation patterns
            r"\bemerging\b",
            r"\binnovation\b",
            r"\br&d\b",
            r"\bnew technology\b",
            r"\bcutting edge\b",
            r"\bexperimental\b",
            r"\bprototype\b",
            r"\bhype\b",
            r"\bmaturity\b",
            r"\breadiness\b",
            r"\bquantum\b",
            r"\bfuture\b",
            r"\bhorizon\b",
            # Document types
            r"\bpoc\b",
            r"\bproof of concept\b",
            r"\btechnology assessment\b",
            r"\binnovation brief\b",
        ],
        "catalyst": [
            # Communications patterns
            r"\binternal communications\b",
            r"\bmessaging\b",
            r"\bnarrative\b",
            r"\bemployee engagement\b",
            r"\bannouncement\b",
            r"\ball-hands\b",
            r"\btown hall\b",
            r"\binternal marketing\b",
            r"\bai anxiety\b",
            r"\btransparency\b",
            r"\bemail\b",
            # Document types
            r"\bcommunication plan\b",
            r"\bmessaging template\b",
            r"\bfaq\b",
        ],
        "scholar": [
            # L&D patterns
            r"\btraining\b",
            r"\blearning\b",
            r"\bl&d\b",
            r"\benablement\b",
            r"\bcurriculum\b",
            r"\bcourse\b",
            r"\bworkshop\b",
            r"\bcertification\b",
            r"\bchampion program\b",
            r"\bskill development\b",
            r"\badult learning\b",
            r"\bcapability building\b",
            r"\bonboarding\b",
            # Document types
            r"\btraining material\b",
            r"\bcourse outline\b",
            r"\blearning path\b",
            r"\bquiz\b",
            r"\bassessment\b",
        ],
        "echo": [
            # Brand voice patterns
            r"\bbrand voice\b",
            r"\bstyle\b",
            r"\btone\b",
            r"\bvoice analysis\b",
            r"\bai emulation\b",
            r"\bwriting style\b",
            r"\bvoice profile\b",
            r"\bbrand guidelines\b",
            r"\btone of voice\b",
            r"\bstyle guide\b",
            r"\bcommunication style\b",
            r"\bbrand consistency\b",
        ],
        "nexus": [
            # Systems thinking patterns
            r"\bsystems thinking\b",
            r"\bfeedback loop\b",
            r"\bleverage point\b",
            r"\bunintended consequence\b",
            r"\binterconnection\b",
            r"\bcomplexity\b",
            r"\bsecond-order effect\b",
            r"\bsystem dynamics\b",
            r"\barchetype\b",
            r"\breinforcing loop\b",
            r"\bbalancing loop\b",
            r"\bmental model\b",
            r"\broot cause\b",
            r"\bholistic\b",
            r"\bripple effect\b",
            # Document types
            r"\bcausal loop\b",
            r"\bsystem map\b",
        ],
        "manual": [
            # Platform documentation patterns
            r"\bthesis\b",
            r"\bplatform\b",
            r"\bfeature\b",
            r"\bhelp\b",
            r"\btutorial\b",
            r"\bhow.?to\b",
            r"\bguide\b",
            r"\bdocumentation\b",
            r"\bonboarding\b",
            r"\bquick.?start\b",
            r"\bfaq\b",
            r"\btroubleshooting\b",
            r"\bnavigation\b",
            r"\bui\b",
            r"\binterface\b",
            r"\bworkflow\b",
            r"\buser.?guide\b",
            r"\badmin.?guide\b",
            r"\bknowledge.?base\b",
            r"\bmeeting.?room\b",
            r"\bagent.?roster\b",
            r"\bdig.?deeper\b",
        ],
    }

    # Agent display names for prompts
    AGENT_DESCRIPTIONS = {
        "atlas": "Research agent for GenAI research, consulting approaches, case studies",
        "capital": "Finance agent for ROI analysis, budgets, invoices, financial documents",
        "guardian": "IT/Governance agent for security, compliance, infrastructure, policy",
        "counselor": "Legal agent for contracts, NDAs, MSAs, licensing, legal documents",
        "oracle": "Meeting analyst for transcripts, interview notes, stakeholder feedback",
        "sage": "People/Change agent for HR, change management, adoption, employee concerns",
        "strategist": "Executive strategy for C-suite materials, board presentations, roadmaps",
        "architect": "Technical architecture for specs, API docs, system designs",
        "operator": "Operations for SOPs, process maps, workflow documentation",
        "pioneer": "Innovation/R&D for POCs, technology assessments, emerging tech",
        "catalyst": "Internal communications for messaging templates, announcements, FAQs",
        "scholar": "L&D for training materials, courses, learning content",
        "echo": "Brand voice for style guides, tone guidelines, voice profiles",
        "nexus": "Systems thinking for causal diagrams, complexity analysis",
        "manual": "Documentation assistant for platform help, tutorials, feature explanations",
    }

    def __init__(self, anthropic_client: Optional[anthropic.Anthropic] = None):
        """Initialize classifier with optional Anthropic client."""
        self.anthropic = anthropic_client
        self.supabase = get_supabase()
        self._agent_id_cache: dict[str, str] = {}

    def _get_agent_id(self, agent_name: str) -> Optional[str]:
        """Get agent UUID from name, with caching."""
        if agent_name in self._agent_id_cache:
            return self._agent_id_cache[agent_name]

        try:
            result = self.supabase.table("agents").select("id").eq("name", agent_name).execute()
            if result.data:
                agent_id = result.data[0]["id"]
                self._agent_id_cache[agent_name] = agent_id
                return agent_id
        except Exception as e:
            logger.error(f"Failed to get agent ID for {agent_name}: {e}")

        return None

    def _score_keywords(self, text: str) -> dict[str, float]:
        """Score text against keyword patterns for each agent.

        Returns normalized scores (0.0 - 1.0) for each agent.
        """
        text_lower = text.lower()
        raw_scores: dict[str, int] = {}
        max_score = 0

        for agent, patterns in self.AGENT_KEYWORDS.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, text_lower, re.IGNORECASE))
                score += matches
            if score > 0:
                raw_scores[agent] = score
                max_score = max(max_score, score)

        # Normalize scores to 0.0 - 1.0
        if max_score == 0:
            return {}

        normalized = {}
        for agent, score in raw_scores.items():
            # Use logarithmic scaling to avoid extreme values
            # 1 match = 0.4, 2 matches = 0.6, 4+ matches = 0.8+
            normalized[agent] = min(0.95, 0.3 + (score / max_score) * 0.5 + (min(score, 5) * 0.05))

        return normalized

    def _has_clear_winner(self, scores: dict[str, float]) -> bool:
        """Check if keyword scoring has a clear winner."""
        if not scores:
            return False

        sorted_scores = sorted(scores.values(), reverse=True)
        if len(sorted_scores) == 1:
            return sorted_scores[0] >= self.MEDIUM_CONFIDENCE_THRESHOLD

        # Clear winner if top score is significantly higher than second
        return (
            sorted_scores[0] >= self.HIGH_CONFIDENCE_THRESHOLD
            and sorted_scores[0] - sorted_scores[1] >= 0.20
        )

    def _build_llm_prompt(self, sample_text: str, candidates: Optional[list[str]] = None) -> str:
        """Build the LLM classification prompt.

        Args:
            sample_text: Document text to classify
            candidates: Optional list of candidate agents from keyword scoring.
                       If provided, only these agents are considered (saves tokens).
                       If None, all agents are sent (fallback behavior).
        """
        # If we have candidates from keyword scoring, only send those (more efficient)
        if candidates and len(candidates) >= 2:
            agent_list = "\n".join(
                [
                    f"- {name}: {self.AGENT_DESCRIPTIONS.get(name, 'Specialist agent')}"
                    for name in candidates[:6]  # Max 6 candidates to keep prompt small
                ]
            )
            agent_note = "From these candidate agents, select the most relevant:"
        else:
            # Fallback: send all agents (less efficient but comprehensive)
            agent_list = "\n".join(
                [f"- {name}: {desc}" for name, desc in self.AGENT_DESCRIPTIONS.items()]
            )
            agent_note = "Select which agents should have access to this document:"

        return f"""Classify this document for agent relevance.

{agent_note}
{agent_list}

Document excerpt:
{sample_text[:2500]}

Return JSON with the most relevant agents (max 3):
{{"agents": [{{"name": "agent_name", "confidence": 0.8, "reason": "brief reason"}}], "document_type": "type"}}"""

    async def _classify_with_llm(
        self, sample_text: str, candidates: Optional[list[str]] = None
    ) -> tuple[dict[str, float], str, int]:
        """Use Claude Haiku for LLM-based classification.

        Args:
            sample_text: Document text to classify
            candidates: Optional list of candidate agents from keyword scoring

        Returns:
            Tuple of (scores dict, detected_type, tokens_used)
        """
        if not self.anthropic:
            logger.warning("No Anthropic client available for LLM classification")
            return {}, "unknown", 0

        try:
            prompt = self._build_llm_prompt(sample_text, candidates)

            response = self.anthropic.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}],
            )

            result_text = response.content[0].text.strip()
            tokens_used = response.usage.input_tokens + response.usage.output_tokens

            # Parse JSON response
            import json

            # Handle potential markdown code blocks
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]

            data = json.loads(result_text)

            scores = {}
            for agent_info in data.get("agents", []):
                agent_name = agent_info.get("name", "").lower()
                confidence = float(agent_info.get("confidence", 0.0))
                if (
                    agent_name in self.AGENT_KEYWORDS
                    and confidence >= self.LOW_CONFIDENCE_THRESHOLD
                ):
                    scores[agent_name] = confidence

            detected_type = data.get("document_type", "unknown")

            return scores, detected_type, tokens_used

        except Exception as e:
            logger.error(f"LLM classification failed: {e}")
            return {}, "unknown", 0

    def _determine_review_needed(
        self, classifications: list[AgentClassification]
    ) -> tuple[bool, Optional[str]]:
        """Determine if user review is needed.

        Returns:
            Tuple of (needs_review, reason)
        """
        if not classifications:
            return True, "No confident agent matches found"

        top = classifications[0]

        # High confidence - auto-tag, no review
        if top.confidence >= self.HIGH_CONFIDENCE_THRESHOLD:
            return False, None

        # Medium confidence with close second - needs review
        if len(classifications) > 1:
            second = classifications[1]
            if top.confidence - second.confidence < 0.15:
                return True, f"Close match between {top.agent_name} and {second.agent_name}"

        # Medium confidence single match - auto-tag with notification
        if top.confidence >= self.MEDIUM_CONFIDENCE_THRESHOLD:
            return False, None

        # Low confidence - needs review
        return True, f"Low confidence ({top.confidence:.0%}) for {top.agent_name}"

    async def classify(
        self, document_id: str, sample_chunks: list[str]
    ) -> DocumentClassificationResult:
        """Classify a document for agent relevance.

        Args:
            document_id: UUID of the document
            sample_chunks: First 3 chunks of document text

        Returns:
            DocumentClassificationResult with agent classifications
        """
        start_time = time.time()
        combined_text = "\n\n".join(sample_chunks)

        # Phase 1: Keyword scoring
        keyword_scores = self._score_keywords(combined_text)
        logger.info(f"Keyword scores for document {document_id}: {keyword_scores}")

        method = "keyword"
        detected_type = "unknown"
        tokens_used = 0
        llm_scores: dict[str, float] = {}

        # Phase 2: LLM classification if ambiguous
        if not self._has_clear_winner(keyword_scores):
            method = "hybrid"
            # Pass keyword candidates to LLM for more efficient classification
            candidates = list(keyword_scores.keys()) if keyword_scores else None
            llm_scores, detected_type, tokens_used = await self._classify_with_llm(
                combined_text, candidates
            )
            logger.info(f"LLM scores for document {document_id}: {llm_scores}")

        # Merge scores (LLM takes precedence for ambiguous cases)
        final_scores = keyword_scores.copy()
        for agent, score in llm_scores.items():
            if agent not in final_scores or llm_scores.get(agent, 0) > keyword_scores.get(agent, 0):
                final_scores[agent] = score

        # Build classifications list
        classifications: list[AgentClassification] = []
        for agent_name, confidence in sorted(
            final_scores.items(), key=lambda x: x[1], reverse=True
        ):
            if confidence < self.LOW_CONFIDENCE_THRESHOLD:
                continue

            agent_id = self._get_agent_id(agent_name)
            if not agent_id:
                continue

            classifications.append(
                AgentClassification(
                    agent_id=agent_id,
                    agent_name=agent_name,
                    confidence=confidence,
                    relevance_score=confidence,  # Use confidence as relevance
                    reason=f"Matched via {method} classification",
                )
            )

        # Limit to top 3 agents
        classifications = classifications[:3]

        # Determine if review needed
        needs_review, review_reason = self._determine_review_needed(classifications)

        processing_time_ms = int((time.time() - start_time) * 1000)

        return DocumentClassificationResult(
            document_id=document_id,
            detected_type=detected_type,
            classifications=classifications,
            requires_user_review=needs_review,
            review_reason=review_reason,
            classification_method=method,
            model_used="claude-3-5-haiku-20241022" if method == "hybrid" else None,
            tokens_used=tokens_used,
            processing_time_ms=processing_time_ms,
        )

    async def store_classification(
        self, result: DocumentClassificationResult, auto_link_agents: bool = True
    ) -> bool:
        """Store classification result in database.

        Args:
            result: Classification result to store
            auto_link_agents: If True, create agent_knowledge_base links for confident matches

        Returns:
            True if successful
        """
        try:
            # Store in document_classifications table
            classification_data = {
                "document_id": result.document_id,
                "detected_type": result.detected_type,
                "classification_method": result.classification_method,
                "model_used": result.model_used,
                "tokens_used": result.tokens_used,
                "processing_time_ms": result.processing_time_ms,
                "raw_scores": {c.agent_name: c.confidence for c in result.classifications},
                "sample_chunks_used": 3,
                "status": "needs_review" if result.requires_user_review else "completed",
                "requires_user_review": result.requires_user_review,
                "review_reason": result.review_reason,
            }

            self.supabase.table("document_classifications").insert(classification_data).execute()

            # Auto-link agents if confident and enabled
            if auto_link_agents and not result.requires_user_review:
                for classification in result.classifications:
                    if classification.confidence >= self.MEDIUM_CONFIDENCE_THRESHOLD:
                        await self._link_agent_to_document(
                            document_id=result.document_id,
                            classification=classification,
                            source=result.classification_method,
                        )

            logger.info(
                f"Stored classification for document {result.document_id}: "
                f"{len(result.classifications)} agents, review_needed={result.requires_user_review}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to store classification for {result.document_id}: {e}")
            return False

    async def _link_agent_to_document(
        self, document_id: str, classification: AgentClassification, source: str
    ) -> bool:
        """Create agent_knowledge_base link with relevance scoring."""
        try:
            # Check if link already exists
            existing = (
                self.supabase.table("agent_knowledge_base")
                .select("id")
                .eq("document_id", document_id)
                .eq("agent_id", classification.agent_id)
                .execute()
            )

            if existing.data:
                # Update existing link
                self.supabase.table("agent_knowledge_base").update(
                    {
                        "relevance_score": classification.relevance_score,
                        "classification_source": f"auto_{source}",
                        "classification_confidence": classification.confidence,
                        "classification_reason": classification.reason,
                        "user_confirmed": False,
                    }
                ).eq("id", existing.data[0]["id"]).execute()
            else:
                # Create new link
                self.supabase.table("agent_knowledge_base").insert(
                    {
                        "document_id": document_id,
                        "agent_id": classification.agent_id,
                        "relevance_score": classification.relevance_score,
                        "classification_source": f"auto_{source}",
                        "classification_confidence": classification.confidence,
                        "classification_reason": classification.reason,
                        "user_confirmed": False,
                        "priority": 0,
                    }
                ).execute()

            logger.info(f"Linked agent {classification.agent_name} to document {document_id}")
            return True

        except Exception as e:
            logger.error(
                f"Failed to link agent {classification.agent_name} to document {document_id}: {e}"
            )
            return False


# Singleton instance
_classifier: Optional[DocumentClassifier] = None


def get_classifier(anthropic_client: Optional[anthropic.Anthropic] = None) -> DocumentClassifier:
    """Get or create classifier singleton."""
    global _classifier
    if _classifier is None:
        _classifier = DocumentClassifier(anthropic_client)
    return _classifier


async def classify_document_for_agents(
    document_id: str,
    chunks: list[str],
    anthropic_client: Optional[anthropic.Anthropic] = None,
    auto_store: bool = True,
) -> DocumentClassificationResult:
    """Convenience function to classify a document.

    Args:
        document_id: UUID of the document
        chunks: Document chunks (uses first 3)
        anthropic_client: Optional Anthropic client for LLM classification
        auto_store: If True, automatically store results in database

    Returns:
        DocumentClassificationResult
    """
    classifier = get_classifier(anthropic_client)
    result = await classifier.classify(document_id, chunks[:3])

    if auto_store:
        await classifier.store_classification(result)

    return result
