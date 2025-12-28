"""
Agent Observer Service

Monitors agent conversations to:
- Understand what topics agents are discussing
- Detect knowledge gaps (questions not well-answered)
- Identify patterns that should trigger research
- Enable anticipatory research based on stakeholder activity
"""

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Optional

from database import get_supabase
from logger_config import get_logger

logger = get_logger(__name__)

supabase = get_supabase()


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class AgentTopicSummary:
    """Summary of topics an agent has been discussing."""
    agent_name: str
    topics: list[str]
    open_questions: list[str]
    conversation_count: int
    last_active: str


@dataclass
class KnowledgeGap:
    """A gap in agent knowledge that needs research."""
    topic: str
    question: str
    source_agent: str
    source_conversation_id: Optional[str]
    uncertainty_signals: list[str]
    gap_type: str  # missing_data, outdated_info, no_benchmarks, needs_research
    priority: int
    occurrence_count: int


@dataclass
class PlatformContext:
    """Overall platform context for research prioritization."""
    recent_conversations: list[dict]
    unanswered_questions: list[KnowledgeGap]
    active_stakeholders: list[dict]
    pending_opportunities: list[dict]
    agent_topics: list[AgentTopicSummary]


# ============================================================================
# UNCERTAINTY DETECTION
# ============================================================================

# Phrases that indicate an agent was uncertain in their response
UNCERTAINTY_SIGNALS = [
    "i'm not sure",
    "i don't have specific",
    "i don't have current",
    "based on my training",
    "i would need to research",
    "i don't have access to",
    "i can't provide specific",
    "this may vary",
    "i recommend consulting",
    "for the most current",
    "i don't have data on",
    "i'm unable to confirm",
    "specific figures would require",
    "i would need more information",
    "i cannot access",
    "my knowledge cutoff",
    "as of my last update",
]

# Phrases that indicate a follow-up question (gap signal)
FOLLOWUP_SIGNALS = [
    "can you provide more detail",
    "do you have specific",
    "what about",
    "can you elaborate",
    "i need more specific",
    "that's not quite what i meant",
    "can you be more specific",
    "do you have examples",
    "what are the actual numbers",
]


def detect_uncertainty_in_response(response_text: str) -> list[str]:
    """
    Detect uncertainty signals in an agent response.

    Returns list of matched uncertainty phrases.
    """
    response_lower = response_text.lower()
    matched = []

    for signal in UNCERTAINTY_SIGNALS:
        if signal in response_lower:
            matched.append(signal)

    return matched


def detect_followup_question(user_message: str) -> bool:
    """Check if a user message is a follow-up indicating incomplete answer."""
    message_lower = user_message.lower()

    for signal in FOLLOWUP_SIGNALS:
        if signal in message_lower:
            return True

    return False


# ============================================================================
# CONVERSATION ANALYSIS
# ============================================================================

async def get_recent_agent_conversations(
    days: int = 7,
    client_id: Optional[str] = None
) -> list[dict]:
    """
    Get recent conversations where agents participated.
    """
    try:
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

        query = supabase.table('conversations')\
            .select('id, title, agent_name, updated_at, client_id')\
            .gte('updated_at', since)\
            .not_.is_('agent_name', 'null')\
            .order('updated_at', desc=True)

        if client_id:
            query = query.eq('client_id', client_id)

        result = query.execute()

        return result.data or []

    except Exception as e:
        logger.error(f"Failed to get recent conversations: {e}")
        return []


async def analyze_conversation_for_gaps(
    conversation_id: str
) -> list[KnowledgeGap]:
    """
    Analyze a conversation for knowledge gaps.
    """
    gaps = []

    try:
        # Get conversation messages
        result = supabase.table('messages')\
            .select('role, content, created_at')\
            .eq('conversation_id', conversation_id)\
            .order('created_at')\
            .execute()

        messages = result.data or []

        # Get conversation metadata
        conv_result = supabase.table('conversations')\
            .select('agent_name, title, client_id')\
            .eq('id', conversation_id)\
            .single()\
            .execute()

        conv = conv_result.data
        agent_name = conv.get('agent_name') if conv else 'unknown'
        client_id = conv.get('client_id') if conv else None

        # Analyze message pairs (user question -> agent response)
        for i, msg in enumerate(messages):
            if msg['role'] == 'assistant':
                uncertainty = detect_uncertainty_in_response(msg['content'])

                if uncertainty:
                    # Get the preceding user message for context
                    user_question = ""
                    if i > 0 and messages[i-1]['role'] == 'user':
                        user_question = messages[i-1]['content']

                    # Extract topic from question (first 100 chars)
                    topic = user_question[:100] if user_question else "Unknown topic"

                    gap = KnowledgeGap(
                        topic=topic,
                        question=user_question,
                        source_agent=agent_name,
                        source_conversation_id=conversation_id,
                        uncertainty_signals=uncertainty,
                        gap_type='needs_research',
                        priority=5,
                        occurrence_count=1
                    )
                    gaps.append(gap)

                # Check if next message is a follow-up
                if i + 1 < len(messages) and messages[i + 1]['role'] == 'user':
                    next_msg = messages[i + 1]['content']
                    if detect_followup_question(next_msg):
                        gap = KnowledgeGap(
                            topic=msg['content'][:100],
                            question=next_msg,
                            source_agent=agent_name,
                            source_conversation_id=conversation_id,
                            uncertainty_signals=['follow_up_question'],
                            gap_type='incomplete_answer',
                            priority=6,  # Higher priority for explicit follow-ups
                            occurrence_count=1
                        )
                        gaps.append(gap)

    except Exception as e:
        logger.error(f"Failed to analyze conversation {conversation_id}: {e}")

    return gaps


# ============================================================================
# TOPIC EXTRACTION
# ============================================================================

async def summarize_agent_focus_areas(
    days: int = 7,
    client_id: Optional[str] = None
) -> list[AgentTopicSummary]:
    """
    Summarize what each agent has been focusing on.
    """
    summaries = []

    try:
        # Get conversations grouped by agent
        conversations = await get_recent_agent_conversations(days, client_id)

        # Group by agent
        by_agent: dict[str, list[dict]] = {}
        for conv in conversations:
            agent = conv.get('agent_name')
            if agent:
                if agent not in by_agent:
                    by_agent[agent] = []
                by_agent[agent].append(conv)

        # Summarize each agent
        for agent_name, convs in by_agent.items():
            # Extract topics from conversation titles
            topics = list(set(
                conv.get('title', 'Unknown')[:50]
                for conv in convs
                if conv.get('title')
            ))[:10]

            # Get last active time
            last_active = max(
                conv.get('updated_at', '')
                for conv in convs
            ) if convs else ''

            summary = AgentTopicSummary(
                agent_name=agent_name,
                topics=topics,
                open_questions=[],  # Would need deeper analysis
                conversation_count=len(convs),
                last_active=last_active
            )
            summaries.append(summary)

    except Exception as e:
        logger.error(f"Failed to summarize agent focus areas: {e}")

    return summaries


# ============================================================================
# GAP MANAGEMENT
# ============================================================================

async def identify_knowledge_gaps(
    client_id: Optional[str] = None,
    days: int = 7
) -> list[KnowledgeGap]:
    """
    Identify knowledge gaps across all recent agent conversations.
    """
    all_gaps = []

    try:
        conversations = await get_recent_agent_conversations(days, client_id)

        for conv in conversations[:50]:  # Limit to 50 recent conversations
            gaps = await analyze_conversation_for_gaps(conv['id'])
            all_gaps.extend(gaps)

    except Exception as e:
        logger.error(f"Failed to identify knowledge gaps: {e}")

    return all_gaps


async def save_knowledge_gap(gap: KnowledgeGap, client_id: Optional[str] = None):
    """
    Save a knowledge gap to the database.

    Checks for existing similar gaps and increments occurrence count.
    """
    try:
        # Check for existing similar gap
        existing = supabase.table('knowledge_gaps')\
            .select('id, occurrence_count')\
            .eq('topic', gap.topic[:255])\
            .eq('source_agent', gap.source_agent)\
            .eq('status', 'open')\
            .limit(1)\
            .execute()

        if existing.data:
            # Increment occurrence count
            gap_id = existing.data[0]['id']
            new_count = existing.data[0]['occurrence_count'] + 1

            supabase.table('knowledge_gaps')\
                .update({
                    'occurrence_count': new_count,
                    'priority': min(10, gap.priority + 1),  # Increase priority
                    'updated_at': datetime.now(timezone.utc).isoformat()
                })\
                .eq('id', gap_id)\
                .execute()

            logger.info(f"Updated gap occurrence: {gap.topic[:50]}... (count: {new_count})")

        else:
            # Create new gap
            supabase.table('knowledge_gaps').insert({
                'client_id': client_id,
                'topic': gap.topic[:255],
                'question': gap.question,
                'source_agent': gap.source_agent,
                'source_conversation_id': gap.source_conversation_id,
                'uncertainty_signals': gap.uncertainty_signals,
                'gap_type': gap.gap_type,
                'priority': gap.priority,
                'occurrence_count': 1,
                'status': 'open'
            }).execute()

            logger.info(f"Created new gap: {gap.topic[:50]}...")

    except Exception as e:
        logger.error(f"Failed to save knowledge gap: {e}")


async def get_open_knowledge_gaps(
    client_id: Optional[str] = None,
    limit: int = 10
) -> list[dict]:
    """Get prioritized list of open knowledge gaps."""
    try:
        query = supabase.table('knowledge_gaps')\
            .select('*')\
            .eq('status', 'open')\
            .order('priority', desc=True)\
            .order('occurrence_count', desc=True)\
            .limit(limit)

        if client_id:
            query = query.eq('client_id', client_id)

        result = query.execute()

        return result.data or []

    except Exception as e:
        logger.error(f"Failed to get knowledge gaps: {e}")
        return []


# ============================================================================
# STAKEHOLDER ACTIVITY
# ============================================================================

async def get_active_stakeholders(
    client_id: str,
    days: int = 30
) -> list[dict]:
    """
    Get stakeholders with recent activity (insights, meetings, etc.).
    """
    try:
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

        # Get stakeholders with recent insights
        result = supabase.table('stakeholders')\
            .select('id, name, title, department, sentiment, engagement_score')\
            .eq('client_id', client_id)\
            .order('engagement_score', desc=True)\
            .limit(20)\
            .execute()

        return result.data or []

    except Exception as e:
        logger.error(f"Failed to get active stakeholders: {e}")
        return []


async def get_stakeholder_concerns(
    client_id: str,
    unresolved_only: bool = True
) -> list[dict]:
    """Get stakeholder concerns that might need research."""
    try:
        query = supabase.table('stakeholder_insights')\
            .select('id, content, insight_type, stakeholder_id, created_at')\
            .eq('insight_type', 'concern')

        if unresolved_only:
            query = query.eq('is_resolved', False)

        result = query.order('created_at', desc=True).limit(20).execute()

        return result.data or []

    except Exception as e:
        logger.error(f"Failed to get stakeholder concerns: {e}")
        return []


# ============================================================================
# ANTICIPATORY RESEARCH TRIGGERS
# ============================================================================

async def get_anticipatory_research_topics(
    client_id: str
) -> list[dict]:
    """
    Identify topics that should be researched proactively based on:
    - New stakeholders added
    - ROI opportunities in evaluation
    - Recurring agent topics
    - Stakeholder concerns
    """
    topics = []

    try:
        # Check for new stakeholders (last 7 days)
        week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

        new_stakeholders = supabase.table('stakeholders')\
            .select('id, name, department, title')\
            .eq('client_id', client_id)\
            .gte('created_at', week_ago)\
            .execute()

        for stakeholder in new_stakeholders.data or []:
            dept = stakeholder.get('department', 'General')
            topics.append({
                'topic': f"AI use cases for {dept} department",
                'trigger': 'new_stakeholder',
                'context': stakeholder,
                'priority': 7
            })

        # Check for ROI opportunities being evaluated
        opportunities = supabase.table('roi_opportunities')\
            .select('id, title, department, estimated_value')\
            .eq('status', 'evaluating')\
            .execute()

        for opp in opportunities.data or []:
            topics.append({
                'topic': f"ROI benchmarks for {opp.get('title', 'AI initiative')}",
                'trigger': 'roi_opportunity',
                'context': opp,
                'priority': 8
            })

        # Check for unresolved stakeholder concerns
        concerns = await get_stakeholder_concerns(client_id, unresolved_only=True)

        for concern in concerns[:5]:  # Top 5 concerns
            topics.append({
                'topic': concern.get('content', 'Unknown concern')[:100],
                'trigger': 'stakeholder_concern',
                'context': concern,
                'priority': 6
            })

    except Exception as e:
        logger.error(f"Failed to get anticipatory topics: {e}")

    # Sort by priority
    topics.sort(key=lambda t: t['priority'], reverse=True)

    return topics


# ============================================================================
# MAIN OBSERVER FUNCTION
# ============================================================================

async def get_platform_context(client_id: Optional[str] = None) -> PlatformContext:
    """
    Get comprehensive platform context for research prioritization.
    """
    # Gather all context in parallel would be ideal, but sequential for now
    recent_conversations = await get_recent_agent_conversations(days=7, client_id=client_id)
    knowledge_gaps = await identify_knowledge_gaps(client_id=client_id, days=7)
    agent_topics = await summarize_agent_focus_areas(days=7, client_id=client_id)

    # Get stakeholder and opportunity data if client specified
    active_stakeholders = []
    pending_opportunities = []

    if client_id:
        active_stakeholders = await get_active_stakeholders(client_id, days=30)

        try:
            opps = supabase.table('roi_opportunities')\
                .select('*')\
                .in_('status', ['identified', 'evaluating'])\
                .execute()
            pending_opportunities = opps.data or []
        except Exception as e:
            logger.error(f"Failed to get opportunities: {e}")

    # Convert gaps to dataclass instances if needed
    gap_objects = []
    for gap in knowledge_gaps:
        if isinstance(gap, KnowledgeGap):
            gap_objects.append(gap)

    return PlatformContext(
        recent_conversations=recent_conversations,
        unanswered_questions=gap_objects,
        active_stakeholders=active_stakeholders,
        pending_opportunities=pending_opportunities,
        agent_topics=agent_topics
    )


async def run_observation_cycle(client_id: Optional[str] = None):
    """
    Run a full observation cycle:
    1. Scan recent conversations
    2. Detect knowledge gaps
    3. Save gaps to database
    4. Return summary
    """
    logger.info("Starting observation cycle...")

    gaps = await identify_knowledge_gaps(client_id=client_id, days=7)

    # Save new gaps
    for gap in gaps:
        await save_knowledge_gap(gap, client_id)

    logger.info(f"Observation cycle complete. Found {len(gaps)} potential gaps.")

    return {
        'gaps_found': len(gaps),
        'timestamp': datetime.now(timezone.utc).isoformat()
    }
