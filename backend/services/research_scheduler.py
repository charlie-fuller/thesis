"""
Atlas Research Scheduler

This module provides background job scheduling for automated research tasks.
Atlas monitors platform context (stakeholder concerns, agent gaps, ROI opportunities)
and proactively generates research that is auto-published to the knowledge base.

Architecture:
- Daily scheduled research based on configurable focus areas
- Context-driven topic selection from stakeholder concerns and knowledge gaps
- Web search integration for fresh research
- Auto-publish to agent knowledge bases
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from database import get_supabase
from logger_config import get_logger

logger = get_logger(__name__)

# Get centralized Supabase client
supabase = get_supabase()

# Global scheduler instance
research_scheduler: Optional[BackgroundScheduler] = None


# ============================================================================
# DATA MODELS
# ============================================================================

class ResearchTopic:
    """Represents a topic to research."""

    def __init__(
        self,
        topic: str,
        query: str,
        focus_area: str,
        priority: int = 5,
        research_type: str = "scheduled",
        context: Optional[dict] = None,
        client_id: Optional[str] = None
    ):
        self.topic = topic
        self.query = query
        self.focus_area = focus_area
        self.priority = priority
        self.research_type = research_type
        self.context = context or {}
        self.client_id = client_id


class ResearchResult:
    """Result of a research execution."""

    def __init__(
        self,
        task_id: str,
        content: str,
        summary: str,
        web_sources: list,
        document_id: Optional[str] = None,
        success: bool = True,
        error: Optional[str] = None
    ):
        self.task_id = task_id
        self.content = content
        self.summary = summary
        self.web_sources = web_sources
        self.document_id = document_id
        self.success = success
        self.error = error


# ============================================================================
# RESEARCH TASK MANAGEMENT
# ============================================================================

def create_research_task(
    topic: ResearchTopic,
    client_id: Optional[str] = None
) -> str:
    """
    Create a research task in the database.

    Returns:
        str: The task ID
    """
    task_id = str(uuid4())

    try:
        supabase.table('research_tasks').insert({
            'id': task_id,
            'client_id': client_id,
            'topic': topic.topic,
            'query': topic.query,
            'focus_area': topic.focus_area,
            'research_type': topic.research_type,
            'priority': topic.priority,
            'context': topic.context,
            'status': 'pending'
        }).execute()

        logger.info(f"Created research task {task_id}: {topic.topic}")
        return task_id

    except Exception as e:
        logger.error(f"Failed to create research task: {e}")
        raise


def update_research_task_status(
    task_id: str,
    status: str,
    result_content: Optional[str] = None,
    result_summary: Optional[str] = None,
    result_document_id: Optional[str] = None,
    web_sources: Optional[list] = None,
    error_message: Optional[str] = None
):
    """Update a research task's status and results."""
    try:
        update_data = {
            'status': status,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }

        if status == 'running':
            update_data['started_at'] = datetime.now(timezone.utc).isoformat()
        elif status in ('completed', 'failed'):
            update_data['completed_at'] = datetime.now(timezone.utc).isoformat()

        if result_content:
            update_data['result_content'] = result_content
        if result_summary:
            update_data['result_summary'] = result_summary
        if result_document_id:
            update_data['result_document_id'] = result_document_id
        if web_sources:
            update_data['web_sources'] = web_sources
        if error_message:
            update_data['error_message'] = error_message

        supabase.table('research_tasks').update(update_data).eq('id', task_id).execute()

    except Exception as e:
        logger.error(f"Failed to update research task {task_id}: {e}")


# ============================================================================
# SCHEDULE MANAGEMENT
# ============================================================================

def get_todays_schedule(client_id: Optional[str] = None) -> list[dict]:
    """
    Get today's research schedule.

    Returns both global schedule and client-specific schedule if client_id provided.
    """
    try:
        today_dow = datetime.now(timezone.utc).weekday()
        # Convert Python weekday (0=Monday) to SQL weekday (0=Sunday)
        sql_dow = (today_dow + 1) % 7

        # Get global schedule
        global_result = supabase.table('research_schedule')\
            .select('*')\
            .is_('client_id', 'null')\
            .eq('day_of_week', sql_dow)\
            .eq('is_active', True)\
            .order('priority', desc=True)\
            .execute()

        schedules = global_result.data or []

        # Get client-specific schedule if provided
        if client_id:
            client_result = supabase.table('research_schedule')\
                .select('*')\
                .eq('client_id', client_id)\
                .eq('day_of_week', sql_dow)\
                .eq('is_active', True)\
                .order('priority', desc=True)\
                .execute()

            schedules.extend(client_result.data or [])

        return schedules

    except Exception as e:
        logger.error(f"Failed to get today's schedule: {e}")
        return []


def get_all_active_clients() -> list[str]:
    """Get all clients that have active users/conversations."""
    try:
        # Get clients with recent activity (conversations in last 30 days)
        result = supabase.table('conversations')\
            .select('client_id')\
            .gte('updated_at', (datetime.now(timezone.utc).replace(day=1)).isoformat())\
            .execute()

        client_ids = list(set(row['client_id'] for row in result.data if row.get('client_id')))
        return client_ids

    except Exception as e:
        logger.error(f"Failed to get active clients: {e}")
        return []


# ============================================================================
# RESEARCH EXECUTION
# ============================================================================

async def execute_research_task(task_id: str, topic: ResearchTopic) -> ResearchResult:
    """
    Execute a single research task using Atlas.

    This is the core function that:
    1. Calls Atlas with the research query
    2. Optionally performs web search for fresh data
    3. Synthesizes and validates the output
    4. Stores as a document and links to agent KBs
    """
    from agents.atlas import AtlasAgent
    from agents.base_agent import AgentContext
    import anthropic

    try:
        # Mark task as running
        update_research_task_status(task_id, 'running')

        # Initialize Atlas
        anthropic_client = anthropic.Anthropic()
        atlas = AtlasAgent(supabase, anthropic_client)

        # Build context for Atlas
        context = AgentContext(
            user_id="system_atlas",
            client_id=topic.client_id or "global",
            conversation_id=str(uuid4()),
            message_history=[],
            user_message=topic.query,
            memories=[]
        )

        # Execute Atlas research
        logger.info(f"Executing Atlas research for task {task_id}: {topic.topic}")
        response = await atlas.process(context)

        # Generate summary (first 500 chars or first paragraph)
        content = response.content
        summary = content[:500] + "..." if len(content) > 500 else content
        if "\n\n" in content:
            summary = content.split("\n\n")[0]

        # Store as document
        document_id = await store_research_document(
            topic=topic,
            content=content,
            task_id=task_id
        )

        # Update task as completed
        update_research_task_status(
            task_id=task_id,
            status='completed',
            result_content=content,
            result_summary=summary,
            result_document_id=document_id,
            web_sources=[]  # Will be populated when web search is added
        )

        logger.info(f"Research task {task_id} completed successfully")

        return ResearchResult(
            task_id=task_id,
            content=content,
            summary=summary,
            web_sources=[],
            document_id=document_id,
            success=True
        )

    except Exception as e:
        logger.error(f"Research task {task_id} failed: {e}")
        update_research_task_status(
            task_id=task_id,
            status='failed',
            error_message=str(e)
        )
        return ResearchResult(
            task_id=task_id,
            content="",
            summary="",
            web_sources=[],
            success=False,
            error=str(e)
        )


async def store_research_document(
    topic: ResearchTopic,
    content: str,
    task_id: str
) -> Optional[str]:
    """
    Store research output as a document and link to agent KBs.
    """
    try:
        # Generate filename
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        filename = f"atlas_research_{topic.focus_area}_{date_str}.md"

        # Create document record
        doc_result = supabase.table('documents').insert({
            'filename': filename,
            'file_type': 'text/markdown',
            'file_size': len(content.encode('utf-8')),
            'metadata': {
                'generated_by': 'atlas',
                'research_task_id': task_id,
                'topic': topic.topic,
                'focus_area': topic.focus_area,
                'research_type': topic.research_type,
                'generated_at': datetime.now(timezone.utc).isoformat()
            }
        }).execute()

        if not doc_result.data:
            logger.error("Failed to create document record")
            return None

        document_id = doc_result.data[0]['id']

        # Get Atlas agent ID
        atlas_result = supabase.table('agents')\
            .select('id')\
            .eq('name', 'atlas')\
            .single()\
            .execute()

        if atlas_result.data:
            atlas_agent_id = atlas_result.data['id']

            # Link to Atlas knowledge base
            supabase.table('agent_knowledge_base').insert({
                'agent_id': atlas_agent_id,
                'document_id': document_id,
                'priority': topic.priority,
                'notes': f"Auto-generated research: {topic.topic}"
            }).execute()

            # Link to other relevant agents based on topic
            await distribute_to_relevant_agents(document_id, topic, atlas_agent_id)

        logger.info(f"Stored research document {document_id}: {filename}")
        return document_id

    except Exception as e:
        logger.error(f"Failed to store research document: {e}")
        return None


async def distribute_to_relevant_agents(
    document_id: str,
    topic: ResearchTopic,
    exclude_agent_id: str
):
    """
    Link research document to agents relevant to the topic.
    """
    try:
        # Get topic keywords from focus area
        keywords = topic.focus_area.lower().replace('_', ' ').split()

        # Query agent topic mappings
        for keyword in keywords:
            mapping_result = supabase.table('agent_topic_mapping')\
                .select('agent_name, relevance_score')\
                .eq('topic_keyword', keyword)\
                .gte('relevance_score', 0.7)\
                .execute()

            for mapping in mapping_result.data or []:
                agent_name = mapping['agent_name']

                # Get agent ID
                agent_result = supabase.table('agents')\
                    .select('id')\
                    .eq('name', agent_name)\
                    .single()\
                    .execute()

                if agent_result.data and agent_result.data['id'] != exclude_agent_id:
                    agent_id = agent_result.data['id']

                    # Check if link already exists
                    existing = supabase.table('agent_knowledge_base')\
                        .select('id')\
                        .eq('agent_id', agent_id)\
                        .eq('document_id', document_id)\
                        .execute()

                    if not existing.data:
                        supabase.table('agent_knowledge_base').insert({
                            'agent_id': agent_id,
                            'document_id': document_id,
                            'priority': int(topic.priority * mapping['relevance_score']),
                            'notes': f"Cross-linked from Atlas research: {topic.topic}"
                        }).execute()

                        logger.info(f"Linked research to agent {agent_name}")

    except Exception as e:
        logger.error(f"Failed to distribute to agents: {e}")


# ============================================================================
# MAIN SCHEDULER JOB
# ============================================================================

def run_daily_research():
    """
    Main scheduled job that runs daily research.

    This function:
    1. Gets today's research schedule (global + client-specific)
    2. Creates research tasks for each scheduled topic
    3. Executes tasks and stores results
    """
    import asyncio

    try:
        logger.info(f"\n{'='*60}")
        logger.info(f"🔬 Atlas Daily Research Started: {datetime.now(timezone.utc).isoformat()}")
        logger.info(f"{'='*60}")

        # Get today's global schedule
        global_schedule = get_todays_schedule()

        if not global_schedule:
            logger.info("   ℹ️  No research scheduled for today")
            logger.info(f"{'='*60}\n")
            return

        logger.info(f"   📋 Found {len(global_schedule)} scheduled research topic(s)")

        # Process global research
        for schedule in global_schedule:
            try:
                topic = ResearchTopic(
                    topic=schedule.get('description', schedule['focus_area']),
                    query=schedule.get('query_template', f"Research {schedule['focus_area']}"),
                    focus_area=schedule['focus_area'],
                    priority=schedule.get('priority', 5),
                    research_type='scheduled',
                    client_id=schedule.get('client_id')
                )

                task_id = create_research_task(topic, client_id=schedule.get('client_id'))

                # Run async execution in sync context
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(execute_research_task(task_id, topic))
                    if result.success:
                        logger.info(f"   ✅ Completed: {topic.topic}")
                    else:
                        logger.warning(f"   ⚠️  Failed: {topic.topic} - {result.error}")
                finally:
                    loop.close()

            except Exception as topic_error:
                logger.error(f"   ❌ Error processing topic {schedule.get('focus_area')}: {topic_error}")

        # Get active clients and run client-specific research
        active_clients = get_all_active_clients()
        if active_clients:
            logger.info(f"\n   👥 Processing research for {len(active_clients)} active client(s)")

            for client_id in active_clients:
                try:
                    client_schedule = get_todays_schedule(client_id)
                    client_specific = [s for s in client_schedule if s.get('client_id') == client_id]

                    for schedule in client_specific:
                        topic = ResearchTopic(
                            topic=schedule.get('description', schedule['focus_area']),
                            query=schedule.get('query_template', f"Research {schedule['focus_area']}"),
                            focus_area=schedule['focus_area'],
                            priority=schedule.get('priority', 5),
                            research_type='scheduled',
                            client_id=client_id
                        )

                        task_id = create_research_task(topic, client_id=client_id)

                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            result = loop.run_until_complete(execute_research_task(task_id, topic))
                            if result.success:
                                logger.info(f"   ✅ [Client] Completed: {topic.topic}")
                        finally:
                            loop.close()

                except Exception as client_error:
                    logger.error(f"   ❌ Error processing client {client_id}: {client_error}")

        logger.info(f"\n{'='*60}")
        logger.info(f"✅ Atlas Daily Research Completed: {datetime.now(timezone.utc).isoformat()}")
        logger.info(f"{'='*60}\n")

    except Exception as e:
        logger.error(f"\n❌ Fatal error in daily research job: {e}")
        logger.info(f"{'='*60}\n")


# ============================================================================
# MANUAL TRIGGER
# ============================================================================

async def trigger_research_now(
    focus_area: Optional[str] = None,
    client_id: Optional[str] = None,
    custom_query: Optional[str] = None
) -> ResearchResult:
    """
    Manually trigger a research task immediately.

    Args:
        focus_area: Focus area to research (uses schedule template if available)
        client_id: Optional client to research for
        custom_query: Custom research query (overrides schedule template)
    """
    try:
        # If focus_area provided, try to get template from schedule
        query = custom_query
        if focus_area and not custom_query:
            schedule_result = supabase.table('research_schedule')\
                .select('query_template, description')\
                .eq('focus_area', focus_area)\
                .limit(1)\
                .execute()

            if schedule_result.data:
                query = schedule_result.data[0].get('query_template')
                description = schedule_result.data[0].get('description', focus_area)
            else:
                query = f"Research current best practices and developments in {focus_area}"
                description = focus_area
        else:
            description = focus_area or "Custom research"

        topic = ResearchTopic(
            topic=description,
            query=query or f"Research {focus_area}",
            focus_area=focus_area or "manual",
            priority=8,  # Higher priority for manual triggers
            research_type='manual',
            client_id=client_id
        )

        task_id = create_research_task(topic, client_id=client_id)
        result = await execute_research_task(task_id, topic)

        return result

    except Exception as e:
        logger.error(f"Manual research trigger failed: {e}")
        raise


# ============================================================================
# SCHEDULER LIFECYCLE
# ============================================================================

def start_research_scheduler(hour_utc: int = 6, minute: int = 0):
    """
    Start the background scheduler for automated research.

    Args:
        hour_utc: Hour to run daily research (0-23, default 6 AM UTC)
        minute: Minute to run (default 0)
    """
    global research_scheduler

    if research_scheduler is not None and research_scheduler.running:
        logger.warning("⚠️  Research scheduler is already running")
        return

    research_scheduler = BackgroundScheduler(timezone='UTC')

    # Add daily research job
    research_scheduler.add_job(
        func=run_daily_research,
        trigger=CronTrigger(hour=hour_utc, minute=minute),
        id='atlas_daily_research',
        name='Atlas Daily Research',
        replace_existing=True,
        coalesce=True,
        max_instances=1,
        misfire_grace_time=3600  # Allow job to run up to 1 hour late
    )

    research_scheduler.start()

    logger.info(f"\n{'='*60}")
    logger.info("🔬 Atlas Research Scheduler Started")
    logger.info(f"   ⏱️  Daily research at: {hour_utc:02d}:{minute:02d} UTC")
    logger.info(f"   🕐 Started at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    logger.info(f"{'='*60}\n")


def stop_research_scheduler():
    """Stop the research scheduler."""
    global research_scheduler

    if research_scheduler is not None and research_scheduler.running:
        research_scheduler.shutdown(wait=True)
        logger.info("\n🛑 Atlas Research Scheduler Stopped\n")


def get_research_scheduler_status() -> dict:
    """Get the current status of the research scheduler."""
    if research_scheduler is None:
        return {
            'running': False,
            'jobs': []
        }

    jobs = []
    for job in research_scheduler.get_jobs():
        jobs.append({
            'id': job.id,
            'name': job.name,
            'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None
        })

    return {
        'running': research_scheduler.running,
        'jobs': jobs
    }
