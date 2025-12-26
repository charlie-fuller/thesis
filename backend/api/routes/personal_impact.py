"""
Personal Impact Dashboard API
Provides personal metrics and progress tracking for individual users
"""
import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from auth import get_current_user
from database import get_supabase
from logger_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/personal-impact", tags=["personal-impact"])
limiter = Limiter(key_func=get_remote_address)
supabase = get_supabase()

# Learning Systems Thinking dimensions - focusing on quality of design thinking
# These detect evidence of thoughtful instructional design considerations
DESIGN_THINKING_DIMENSIONS = {
    'learner_focus': {
        'label': 'Learner Focus',
        'description': 'Understanding audience needs and context',
        'keywords': [
            'audience', 'learner', 'participant', 'student', 'employee',
            'prior knowledge', 'experience level', 'skill level', 'background',
            'learning style', 'preference', 'motivation', 'engagement',
            'needs', 'challenges', 'pain point', 'constraint', 'barrier',
            'demographic', 'persona', 'target audience', 'end user'
        ]
    },
    'outcome_orientation': {
        'label': 'Outcome Orientation',
        'description': 'Clear objectives and success criteria',
        'keywords': [
            'objective', 'outcome', 'goal', 'competency', 'capability',
            'performance', 'behavior', 'action', 'demonstrate', 'apply',
            'measurable', 'observable', 'criteria', 'standard', 'benchmark',
            'success', 'achievement', 'mastery', 'proficiency',
            'can do', 'will be able', 'by the end'
        ]
    },
    'transfer_application': {
        'label': 'Transfer & Application',
        'description': 'Real-world relevance and job application',
        'keywords': [
            'transfer', 'apply', 'application', 'real world', 'on the job',
            'workplace', 'practical', 'hands-on', 'practice', 'exercise',
            'scenario', 'case study', 'simulation', 'role play',
            'relevant', 'context', 'situation', 'example', 'realistic',
            'workflow', 'task', 'job aid', 'performance support', 'reinforcement'
        ]
    },
    'engagement_design': {
        'label': 'Engagement Design',
        'description': 'Active learning and interaction',
        'keywords': [
            'engage', 'engagement', 'interactive', 'interaction', 'activity',
            'active learning', 'participate', 'involvement', 'collaborate',
            'discuss', 'discussion', 'group', 'team', 'peer',
            'gamif', 'game', 'challenge', 'competition', 'reward',
            'story', 'narrative', 'emotion', 'meaningful', 'relevant'
        ]
    },
    'retention_reinforcement': {
        'label': 'Retention & Reinforcement',
        'description': 'Memory, spacing, and follow-up',
        'keywords': [
            'retention', 'remember', 'recall', 'memory', 'reinforce',
            'repeat', 'practice', 'spacing', 'spaced', 'interval',
            'review', 'refresh', 'follow-up', 'follow up', 'sustain',
            'chunk', 'microlearning', 'bite-size', 'digestible',
            'retrieval', 'quiz', 'test', 'check', 'knowledge check'
        ]
    },
    'feedback_assessment': {
        'label': 'Feedback & Assessment',
        'description': 'Measuring progress and providing feedback',
        'keywords': [
            'feedback', 'assess', 'assessment', 'evaluate', 'measure',
            'progress', 'performance', 'score', 'grade', 'rubric',
            'formative', 'summative', 'diagnostic', 'pre-test', 'post-test',
            'survey', 'reaction', 'satisfaction', 'effectiveness',
            'impact', 'result', 'roi', 'business outcome', 'metric'
        ]
    }
}

# Legacy keywords kept for backward compatibility with methodology-adoption endpoint
ADDIE_PHASES = {
    'analyze': ['analyze', 'analysis', 'needs assessment', 'gap analysis', 'learner analysis', 'task analysis'],
    'design': ['design', 'learning objectives', 'learning outcomes', 'instructional design', 'course design'],
    'develop': ['develop', 'content development', 'course materials', 'learning materials', 'storyboard'],
    'implement': ['implement', 'deliver', 'deployment', 'rollout', 'launch'],
    'evaluate': ['evaluate', 'assessment', 'feedback', 'measurement', 'effectiveness', 'evaluation']
}

BRADBURY_KEYWORDS = [
    'behavior change', 'force multiplier', 'knowledge application', 'impact loop',
    'performance support', 'workflow integration', 'just-in-time', 'practical application'
]

LD_SKILLS = {
    'assessment_design': ['assessment', 'quiz', 'test', 'evaluation', 'rubric', 'scoring'],
    'objective_writing': ['learning objectives', 'learning outcomes', 'objectives', 'outcomes', 'bloom'],
    'instructional_strategy': ['strategy', 'instructional strategy', 'learning strategy', 'teaching method'],
    'content_design': ['content', 'materials', 'resources', 'media', 'multimedia'],
    'facilitation': ['facilitation', 'facilitate', 'training delivery', 'workshop', 'session']
}


def detect_design_thinking_dimensions(content: str) -> Dict[str, bool]:
    """Detect which design thinking dimensions are present in content"""
    content_lower = content.lower()
    detected = {}
    for dimension_key, dimension_data in DESIGN_THINKING_DIMENSIONS.items():
        detected[dimension_key] = any(
            keyword in content_lower for keyword in dimension_data['keywords']
        )
    return detected


def detect_addie_phases(content: str) -> List[str]:
    """Detect which ADDIE phases are mentioned in content"""
    content_lower = content.lower()
    detected = []
    for phase, keywords in ADDIE_PHASES.items():
        if any(keyword in content_lower for keyword in keywords):
            detected.append(phase)
    return detected


def detect_bradbury_principles(content: str) -> int:
    """Count Bradbury Method principles mentioned"""
    content_lower = content.lower()
    return sum(1 for keyword in BRADBURY_KEYWORDS if keyword in content_lower)


def detect_skills_practiced(content: str) -> List[str]:
    """Detect which L&D skills are being practiced"""
    content_lower = content.lower()
    detected = []
    for skill, keywords in LD_SKILLS.items():
        if any(keyword in content_lower for keyword in keywords):
            detected.append(skill)
    return detected


@router.get("/design-velocity")
@limiter.limit("30/minute")
async def get_design_velocity(
    request: Request,
    current_user: dict = Depends(get_current_user),
    time_period: str = 'month'
):
    """
    Get design velocity metrics for the current user

    Tracks:
    - Projects/conversations started
    - Projects completed (conversations with useable output)
    - Average conversation length
    - Trend data over time

    Args:
        time_period: 'week', 'month', or 'all_time'
    """
    try:
        # Calculate date range
        now = datetime.utcnow()
        if time_period == 'week':
            start_date = now - timedelta(days=7)
            weeks_in_period = 1
        elif time_period == 'month':
            start_date = now - timedelta(days=30)
            weeks_in_period = 4
        else:  # all_time
            start_date = datetime(2020, 1, 1)
            weeks_in_period = max(1, ((now - start_date).days // 7))

        # Get user's conversations
        conversations_result = await asyncio.to_thread(
            lambda: supabase.table('conversations').select(
                'id, created_at, useable_output_message_id, turns_to_useable_output'
            ).eq('user_id', current_user['id']).gte(
                'created_at', start_date.isoformat()
            ).execute()
        )

        if not conversations_result.data:
            return {
                'projects_started': 0,
                'projects_completed': 0,
                'completion_rate': 0.0,
                'avg_conversation_turns': 0.0,
                'trend_data': [],
                'time_period': time_period
            }

        # Get message counts for conversations
        conversation_ids = [c['id'] for c in conversations_result.data]
        messages_result = await asyncio.to_thread(
            lambda: supabase.table('messages').select(
                'conversation_id, role'
            ).in_('conversation_id', conversation_ids).execute()
        )

        # Group messages by conversation
        messages_by_conv = defaultdict(list)
        for msg in messages_result.data:
            messages_by_conv[msg['conversation_id']].append(msg)

        # Calculate metrics
        projects_started = len(conversations_result.data)
        projects_completed = sum(1 for c in conversations_result.data if c.get('useable_output_message_id'))

        # Calculate average turns
        turn_counts = []
        for conv in conversations_result.data:
            user_messages = [m for m in messages_by_conv[conv['id']] if m['role'] == 'user']
            if user_messages:
                turn_counts.append(len(user_messages))

        avg_turns = sum(turn_counts) / len(turn_counts) if turn_counts else 0.0
        completion_rate = (projects_completed / projects_started * 100) if projects_started > 0 else 0.0

        # Build trend data by week
        conversations_by_week = defaultdict(lambda: {'started': 0, 'completed': 0})
        for conv in conversations_result.data:
            try:
                created_str = conv['created_at']
                # Handle various timestamp formats from Supabase
                if created_str.endswith('Z'):
                    created_str = created_str.replace('Z', '+00:00')
                elif '+' not in created_str and '-' not in created_str[-6:]:
                    # No timezone info, assume UTC
                    created_str = created_str + '+00:00'
                created = datetime.fromisoformat(created_str)
                week_key = created.strftime('%Y-W%U')
                conversations_by_week[week_key]['started'] += 1
                if conv.get('useable_output_message_id'):
                    conversations_by_week[week_key]['completed'] += 1
            except (ValueError, KeyError) as e:
                logger.warning(f"Could not parse created_at for conversation {conv.get('id')}: {e}")
                continue

        trend_data = [
            {
                'week': week,
                'started': data['started'],
                'completed': data['completed']
            }
            for week, data in sorted(conversations_by_week.items())
        ]

        return {
            'projects_started': projects_started,
            'projects_completed': projects_completed,
            'completion_rate': round(completion_rate, 1),
            'avg_conversation_turns': round(avg_turns, 1),
            'projects_per_week': round(projects_started / weeks_in_period, 1),
            'trend_data': trend_data,
            'time_period': time_period
        }

    except Exception as e:
        logger.exception("Error calculating design velocity", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/methodology-adoption")
@limiter.limit("30/minute")
async def get_methodology_adoption(
    request: Request,
    current_user: dict = Depends(get_current_user),
    time_period: str = 'month'
):
    """
    Track methodology adoption (ADDIE, Bradbury Method)

    Analyzes conversation content to detect:
    - ADDIE phases covered
    - Bradbury Method principles applied
    - Best practices referenced
    """
    try:
        # Calculate date range
        now = datetime.utcnow()
        if time_period == 'week':
            start_date = now - timedelta(days=7)
        elif time_period == 'month':
            start_date = now - timedelta(days=30)
        else:  # all_time
            start_date = datetime(2020, 1, 1)

        # Get user's conversations
        conversations_result = await asyncio.to_thread(
            lambda: supabase.table('conversations').select(
                'id, created_at'
            ).eq('user_id', current_user['id']).gte(
                'created_at', start_date.isoformat()
            ).execute()
        )

        if not conversations_result.data:
            return {
                'addie_phases_used': {},
                'bradbury_mentions': 0,
                'total_conversations': 0,
                'methodology_coverage': 0.0,
                'time_period': time_period
            }

        conversation_ids = [c['id'] for c in conversations_result.data]

        # Get all messages for these conversations
        messages_result = await asyncio.to_thread(
            lambda: supabase.table('messages').select(
                'conversation_id, content, role'
            ).in_('conversation_id', conversation_ids).execute()
        )

        # Analyze messages
        addie_phase_counts = defaultdict(int)
        bradbury_total = 0
        conversations_with_methodology = set()

        for msg in messages_result.data:
            content = msg.get('content', '')

            # Detect ADDIE phases
            phases = detect_addie_phases(content)
            for phase in phases:
                addie_phase_counts[phase] += 1
                conversations_with_methodology.add(msg['conversation_id'])

            # Detect Bradbury principles
            bradbury_count = detect_bradbury_principles(content)
            if bradbury_count > 0:
                bradbury_total += bradbury_count
                conversations_with_methodology.add(msg['conversation_id'])

        total_conversations = len(conversations_result.data)
        methodology_coverage = (len(conversations_with_methodology) / total_conversations * 100) if total_conversations > 0 else 0.0

        return {
            'addie_phases_used': dict(addie_phase_counts),
            'bradbury_mentions': bradbury_total,
            'total_conversations': total_conversations,
            'conversations_with_methodology': len(conversations_with_methodology),
            'methodology_coverage': round(methodology_coverage, 1),
            'time_period': time_period
        }

    except Exception as e:
        logger.exception("Error calculating methodology adoption", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/learning-progress")
@limiter.limit("30/minute")
async def get_learning_progress(
    request: Request,
    current_user: dict = Depends(get_current_user),
    time_period: str = 'month'
):
    """
    Track learning progress and skill development

    Tracks:
    - Topics explored
    - Skills practiced (assessment design, objective writing, etc.)
    - Growth over time
    """
    try:
        # Calculate date range
        now = datetime.utcnow()
        if time_period == 'week':
            start_date = now - timedelta(days=7)
        elif time_period == 'month':
            start_date = now - timedelta(days=30)
        else:  # all_time
            start_date = datetime(2020, 1, 1)

        # Get user's conversations
        conversations_result = await asyncio.to_thread(
            lambda: supabase.table('conversations').select(
                'id, title, created_at'
            ).eq('user_id', current_user['id']).gte(
                'created_at', start_date.isoformat()
            ).execute()
        )

        if not conversations_result.data:
            return {
                'topics_explored': [],
                'skills_practiced': {},
                'total_conversations': 0,
                'growth_trend': [],
                'time_period': time_period
            }

        conversation_ids = [c['id'] for c in conversations_result.data]

        # Get all messages
        messages_result = await asyncio.to_thread(
            lambda: supabase.table('messages').select(
                'conversation_id, content, role, timestamp'
            ).in_('conversation_id', conversation_ids).execute()
        )

        # Track skills practiced
        skill_counts = defaultdict(int)
        skills_by_week = defaultdict(lambda: defaultdict(int))

        for msg in messages_result.data:
            content = msg.get('content', '')
            timestamp = msg.get('timestamp', '')

            # Detect skills
            skills = detect_skills_practiced(content)
            for skill in skills:
                skill_counts[skill] += 1

                # Track by week for growth trend
                if timestamp:
                    msg_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    week_key = msg_time.strftime('%Y-W%U')
                    skills_by_week[week_key][skill] += 1

        # Extract topics from conversation titles
        topics = [c['title'] for c in conversations_result.data if c.get('title')]

        # Build growth trend
        growth_trend = [
            {
                'week': week,
                'skills_practiced': len(skills),
                'total_mentions': sum(skills.values())
            }
            for week, skills in sorted(skills_by_week.items())
        ]

        return {
            'topics_explored': topics[:20],  # Limit to 20 most recent
            'skills_practiced': dict(skill_counts),
            'total_conversations': len(conversations_result.data),
            'unique_skills': len(skill_counts),
            'growth_trend': growth_trend,
            'time_period': time_period
        }

    except Exception as e:
        logger.exception("Error calculating learning progress", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/systems-thinking-score")
@limiter.limit("30/minute")
async def get_systems_thinking_score(
    request: Request,
    current_user: dict = Depends(get_current_user),
    time_period: str = 'month'
):
    """
    Calculate Learning Systems Thinking Score

    Analyzes conversations for evidence of thoughtful instructional design
    across six dimensions:
    - Learner Focus: Understanding audience needs
    - Outcome Orientation: Clear objectives and success criteria
    - Transfer & Application: Real-world relevance
    - Engagement Design: Active learning approaches
    - Retention & Reinforcement: Memory and spacing considerations
    - Feedback & Assessment: Measuring effectiveness
    """
    try:
        # Calculate date range
        now = datetime.utcnow()
        if time_period == 'week':
            start_date = now - timedelta(days=7)
        elif time_period == 'month':
            start_date = now - timedelta(days=30)
        else:  # all_time
            start_date = datetime(2020, 1, 1)

        # Get user's conversations
        conversations_result = await asyncio.to_thread(
            lambda: supabase.table('conversations').select(
                'id, created_at'
            ).eq('user_id', current_user['id']).gte(
                'created_at', start_date.isoformat()
            ).execute()
        )

        if not conversations_result.data:
            return {
                'overall_score': 0,
                'dimensions': {
                    dim_key: {
                        'label': dim_data['label'],
                        'description': dim_data['description'],
                        'score': 0,
                        'conversations_count': 0
                    }
                    for dim_key, dim_data in DESIGN_THINKING_DIMENSIONS.items()
                },
                'total_conversations': 0,
                'conversations_with_design_thinking': 0,
                'time_period': time_period
            }

        conversation_ids = [c['id'] for c in conversations_result.data]

        # Get all user messages for these conversations
        messages_result = await asyncio.to_thread(
            lambda: supabase.table('messages').select(
                'conversation_id, content'
            ).in_('conversation_id', conversation_ids).eq('role', 'user').execute()
        )

        # Combine messages by conversation
        conv_content = defaultdict(str)
        for msg in messages_result.data:
            conv_content[msg['conversation_id']] += ' ' + (msg.get('content', '') or '')

        # Analyze each conversation for design thinking dimensions
        dimension_counts = dict.fromkeys(DESIGN_THINKING_DIMENSIONS.keys(), 0)
        conversations_with_any_dimension = set()

        for conv_id, content in conv_content.items():
            dimensions_detected = detect_design_thinking_dimensions(content)
            for dim_key, detected in dimensions_detected.items():
                if detected:
                    dimension_counts[dim_key] += 1
                    conversations_with_any_dimension.add(conv_id)

        total_conversations = len(conversations_result.data)

        # Calculate scores (percentage of conversations showing each dimension)
        dimensions_result = {}
        for dim_key, dim_data in DESIGN_THINKING_DIMENSIONS.items():
            count = dimension_counts[dim_key]
            score = round((count / total_conversations * 100) if total_conversations > 0 else 0, 1)
            dimensions_result[dim_key] = {
                'label': dim_data['label'],
                'description': dim_data['description'],
                'score': score,
                'conversations_count': count
            }

        # Overall score is average across all dimensions
        dimension_scores = [d['score'] for d in dimensions_result.values()]
        overall_score = round(sum(dimension_scores) / len(dimension_scores), 1) if dimension_scores else 0

        return {
            'overall_score': overall_score,
            'dimensions': dimensions_result,
            'total_conversations': total_conversations,
            'conversations_with_design_thinking': len(conversations_with_any_dimension),
            'time_period': time_period
        }

    except Exception as e:
        logger.exception("Error calculating systems thinking score", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/activity-summary")
@limiter.limit("30/minute")
async def get_activity_summary(
    request: Request,
    current_user: dict = Depends(get_current_user),
    time_period: str = 'month'
):
    """
    Get activity summary for the current user

    Tracks:
    - Total conversations
    - Total messages sent
    - Documents uploaded
    - Images generated
    """
    try:
        # Calculate date range
        now = datetime.utcnow()
        if time_period == 'week':
            start_date = now - timedelta(days=7)
        elif time_period == 'month':
            start_date = now - timedelta(days=30)
        else:  # all_time
            start_date = datetime(2020, 1, 1)

        # Get user's conversations count
        conversations_result = await asyncio.to_thread(
            lambda: supabase.table('conversations').select(
                'id', count='exact'
            ).eq('user_id', current_user['id']).gte(
                'created_at', start_date.isoformat()
            ).execute()
        )
        total_conversations = conversations_result.count or 0

        # Get total messages (user messages only)
        if total_conversations > 0:
            conversation_ids = [c['id'] for c in conversations_result.data]
            messages_result = await asyncio.to_thread(
                lambda: supabase.table('messages').select(
                    'id', count='exact'
                ).in_('conversation_id', conversation_ids).eq('role', 'user').execute()
            )
            total_messages = messages_result.count or 0
        else:
            total_messages = 0

        # Get documents uploaded (documents table uses updated_at, not created_at)
        documents_result = await asyncio.to_thread(
            lambda: supabase.table('documents').select(
                'id', count='exact'
            ).eq('user_id', current_user['id']).gte(
                'updated_at', start_date.isoformat()
            ).execute()
        )
        documents_uploaded = documents_result.count or 0

        # Get images generated (table is conversation_images, not generated_images)
        images_result = await asyncio.to_thread(
            lambda: supabase.table('conversation_images').select(
                'id', count='exact'
            ).eq('user_id', current_user['id']).gte(
                'created_at', start_date.isoformat()
            ).execute()
        )
        images_generated = images_result.count or 0

        return {
            'total_conversations': total_conversations,
            'total_messages': total_messages,
            'documents_uploaded': documents_uploaded,
            'images_generated': images_generated,
            'time_period': time_period
        }

    except Exception as e:
        logger.exception("Error calculating activity summary", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard-summary")
@limiter.limit("30/minute")
async def get_dashboard_summary(
    request: Request,
    current_user: dict = Depends(get_current_user),
    time_period: str = 'month'
):
    """
    Get complete dashboard summary with all metrics
    """
    try:
        # Get all metrics in parallel
        velocity = await get_design_velocity(request, current_user, time_period)
        methodology = await get_methodology_adoption(request, current_user, time_period)
        learning = await get_learning_progress(request, current_user, time_period)

        return {
            'design_velocity': velocity,
            'methodology_adoption': methodology,
            'learning_progress': learning,
            'time_period': time_period,
            'user_id': current_user['id']
        }

    except Exception as e:
        logger.exception("Error generating dashboard summary", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
