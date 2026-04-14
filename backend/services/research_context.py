"""Research Context Service.

Aggregates platform context to determine what Atlas should research:
- Stakeholder concerns drive research priorities
- Knowledge gaps inform topic selection
- ROI opportunities need supporting benchmarks
- Agent activity patterns suggest anticipatory research
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import pb_client as pb
from repositories import research as research_repo
from repositories import misc as misc_repo
from logger_config import get_logger
from services.agent_observer import (
    get_anticipatory_research_topics,
    get_open_knowledge_gaps,
    get_stakeholder_concerns,
)

logger = get_logger(__name__)


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class ResearchTopic:
    """A prioritized research topic."""

    topic: str
    query: str
    focus_area: str
    priority: int
    source: str  # schedule, stakeholder_concern, knowledge_gap, roi_opportunity, anticipatory
    context: dict
    client_id: Optional[str] = None


@dataclass
class ResearchPriorities:
    """Prioritized list of research topics with metadata."""

    topics: list[ResearchTopic]
    total_count: int
    global_count: int
    client_count: int
    generated_at: str


# ============================================================================
# FOCUS AREA DEFINITIONS
# ============================================================================

FOCUS_AREA_QUERIES = {
    "strategic_planning": {
        "base_query": "What are the latest best practices for {topic}? Include C-suite engagement strategies, governance patterns, and case studies from Fortune 500 companies.",
        "keywords": [
            "strategy",
            "governance",
            "executive",
            "c-suite",
            "leadership",
            "transformation",
        ],
    },
    "finance_roi": {
        "base_query": "What are proven ROI benchmarks and metrics for {topic}? Include specific numbers, payback periods, and case studies from comparable organizations.",
        "keywords": [
            "roi",
            "cost",
            "budget",
            "finance",
            "savings",
            "revenue",
            "payback",
            "investment",
        ],
    },
    "governance_compliance": {
        "base_query": "What are current best practices for {topic} in enterprise AI? Include regulatory requirements, security frameworks, and compliance considerations.",
        "keywords": [
            "compliance",
            "governance",
            "security",
            "audit",
            "regulation",
            "policy",
            "risk",
        ],
    },
    "change_management": {
        "base_query": "What does research say about {topic} in AI implementation? Include adoption patterns, failure modes, and success factors.",
        "keywords": [
            "adoption",
            "change",
            "training",
            "culture",
            "resistance",
            "champion",
            "workforce",
        ],
    },
    "technical_architecture": {
        "base_query": "What are enterprise architecture best practices for {topic}? Include integration patterns, scalability considerations, and vendor evaluation criteria.",
        "keywords": [
            "architecture",
            "integration",
            "api",
            "platform",
            "infrastructure",
            "mlops",
            "rag",
        ],
    },
    "innovation_trends": {
        "base_query": "What are the emerging trends and developments in {topic}? Include maturity assessments, hype vs. reality analysis, and practical timelines.",
        "keywords": ["emerging", "trend", "innovation", "future", "new", "latest", "cutting-edge"],
    },
    "general": {
        "base_query": "What are best practices and current research on {topic}? Include evidence-based recommendations and practical implementation guidance.",
        "keywords": [],
    },
}


# ============================================================================
# TOPIC CLASSIFICATION
# ============================================================================


def classify_focus_area(text: str) -> str:
    """Classify text into a focus area based on keywords."""
    text_lower = text.lower()

    for focus_area, config in FOCUS_AREA_QUERIES.items():
        if focus_area == "general":
            continue

        for keyword in config["keywords"]:
            if keyword in text_lower:
                return focus_area

    return "general"


def generate_research_query(topic: str, focus_area: str) -> str:
    """Generate a research query based on topic and focus area."""
    config = FOCUS_AREA_QUERIES.get(focus_area, FOCUS_AREA_QUERIES["general"])
    query_template = config["base_query"]

    return query_template.format(topic=topic)


# ============================================================================
# PRIORITY SCORING
# ============================================================================


def calculate_priority(source: str, context: dict) -> int:
    """Calculate priority score (1-10) based on source and context."""
    base_priorities = {
        "schedule": 5,
        "knowledge_gap": 7,
        "stakeholder_concern": 8,
        "roi_opportunity": 9,
        "anticipatory": 6,
        "manual": 8,
    }

    priority = base_priorities.get(source, 5)

    # Adjust based on context
    if source == "knowledge_gap":
        occurrence = context.get("occurrence_count", 1)
        if occurrence > 3:
            priority += 2
        elif occurrence > 1:
            priority += 1

    if source == "roi_opportunity":
        estimated_value = context.get("estimated_value", 0)
        if estimated_value > 100000:
            priority += 1

    if source == "stakeholder_concern":
        # Could check stakeholder importance/engagement
        pass

    return min(10, max(1, priority))


# ============================================================================
# CONTEXT AGGREGATION
# ============================================================================


async def get_research_priorities(
    client_id: Optional[str] = None, include_global: bool = True, max_topics: int = 10
) -> ResearchPriorities:
    """Get prioritized list of research topics based on platform context.

    Considers:
    1. Scheduled research for today
    2. Open knowledge gaps
    3. Stakeholder concerns
    4. ROI opportunities needing support
    5. Anticipatory research triggers
    """
    topics: list[ResearchTopic] = []

    # 1. Get scheduled research for today (global)
    if include_global:
        scheduled = await get_scheduled_topics_for_today()
        for item in scheduled:
            topics.append(
                ResearchTopic(
                    topic=item.get("description", item["focus_area"]),
                    query=item.get(
                        "query_template",
                        generate_research_query(item["focus_area"], item["focus_area"]),
                    ),
                    focus_area=item["focus_area"],
                    priority=item.get("priority", 5),
                    source="schedule",
                    context=item,
                    client_id=None,  # Global
                )
            )

    # 2. Get open knowledge gaps
    gaps = await get_open_knowledge_gaps(client_id=client_id, limit=5)
    for gap in gaps:
        focus = classify_focus_area(gap.get("question", "") + " " + gap.get("topic", ""))
        topics.append(
            ResearchTopic(
                topic=gap.get("topic", "Unknown"),
                query=generate_research_query(gap.get("question", gap.get("topic", "")), focus),
                focus_area=focus,
                priority=calculate_priority("knowledge_gap", gap),
                source="knowledge_gap",
                context=gap,
                client_id=client_id,
            )
        )

    # 3. Get stakeholder concerns
    if client_id:
        concerns = await get_stakeholder_concerns(client_id, unresolved_only=True)
        for concern in concerns[:3]:
            content = concern.get("content", "")
            focus = classify_focus_area(content)
            topics.append(
                ResearchTopic(
                    topic=content[:100],
                    query=generate_research_query(content, focus),
                    focus_area=focus,
                    priority=calculate_priority("stakeholder_concern", concern),
                    source="stakeholder_concern",
                    context=concern,
                    client_id=client_id,
                )
            )

    # 4. Get anticipatory research topics
    if client_id:
        anticipatory = await get_anticipatory_research_topics(client_id)
        for item in anticipatory[:3]:
            focus = classify_focus_area(item.get("topic", ""))
            topics.append(
                ResearchTopic(
                    topic=item.get("topic", "Unknown"),
                    query=generate_research_query(item.get("topic", ""), focus),
                    focus_area=focus,
                    priority=item.get("priority", 6),
                    source=item.get("trigger", "anticipatory"),
                    context=item.get("context", {}),
                    client_id=client_id,
                )
            )

    # Sort by priority (highest first)
    topics.sort(key=lambda t: t.priority, reverse=True)

    # Limit results
    topics = topics[:max_topics]

    # Count global vs client
    global_count = sum(1 for t in topics if t.client_id is None)
    client_count = sum(1 for t in topics if t.client_id is not None)

    return ResearchPriorities(
        topics=topics,
        total_count=len(topics),
        global_count=global_count,
        client_count=client_count,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


async def get_scheduled_topics_for_today() -> list[dict]:
    """Get today's scheduled research topics from the database."""
    try:
        today_dow = datetime.now(timezone.utc).weekday()
        # Convert Python weekday (0=Monday) to SQL weekday (0=Sunday)
        sql_dow = (today_dow + 1) % 7

        result = pb.get_all(
            "research_schedule",
            filter=f"client_id='' && day_of_week={sql_dow} && is_active=true",
            sort="-priority",
        )

        return result

    except Exception as e:
        logger.error(f"Failed to get scheduled topics: {e}")
        return []


# ============================================================================
# DEDUPLICATION
# ============================================================================


async def has_recent_research(topic: str, focus_area: str, days: int = 7, client_id: Optional[str] = None) -> bool:
    """Check if similar research was done recently.

    Prevents duplicate research on the same topic.
    """
    try:
        since = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)
        since_str = since.isoformat()

        esc_focus = pb.escape_filter(focus_area)
        esc_since = pb.escape_filter(since_str)
        filter_str = f"focus_area='{esc_focus}' && status='completed' && completed_at>='{esc_since}'"

        if client_id:
            esc_cid = pb.escape_filter(client_id)
            filter_str += f" && client_id='{esc_cid}'"

        result = pb.list_records(
            "research_tasks",
            filter=filter_str,
            per_page=1,
        )

        return len(result.get("items", [])) > 0

    except Exception as e:
        logger.error(f"Failed to check recent research: {e}")
        return False


async def filter_duplicate_topics(topics: list[ResearchTopic]) -> list[ResearchTopic]:
    """Filter out topics that have been researched recently."""
    filtered = []

    for topic in topics:
        has_recent = await has_recent_research(
            topic=topic.topic, focus_area=topic.focus_area, days=7, client_id=topic.client_id
        )

        if not has_recent:
            filtered.append(topic)
        else:
            logger.debug(f"Skipping duplicate topic: {topic.topic[:50]}...")

    return filtered


# ============================================================================
# MAIN FUNCTION
# ============================================================================


async def get_next_research_topic(client_id: Optional[str] = None) -> Optional[ResearchTopic]:
    """Get the single highest-priority research topic to execute next."""
    priorities = await get_research_priorities(client_id=client_id, include_global=True, max_topics=5)

    if not priorities.topics:
        return None

    # Filter duplicates
    filtered = await filter_duplicate_topics(priorities.topics)

    if not filtered:
        return None

    return filtered[0]


async def get_research_summary() -> dict:
    """Get a summary of the current research context.

    Useful for admin dashboards.
    """
    try:
        # Count pending tasks
        pending_count = pb.count("research_tasks", filter="status='pending'")

        # Count completed today
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0).isoformat()
        esc_today = pb.escape_filter(today)
        completed_count = pb.count("research_tasks", filter=f"status='completed' && completed_at>='{esc_today}'")

        # Count open gaps
        gaps_count = pb.count("knowledge_gaps", filter="status='open'")

        # Get today's schedule
        scheduled = await get_scheduled_topics_for_today()

        return {
            "pending_tasks": pending_count,
            "completed_today": completed_count,
            "open_gaps": gaps_count,
            "scheduled_today": len(scheduled),
            "scheduled_topics": [s.get("focus_area") for s in scheduled],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get research summary: {e}")
        return {"error": str(e), "generated_at": datetime.now(timezone.utc).isoformat()}
