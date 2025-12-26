"""
Learning Outcomes Routes
Track expected vs actual outcomes for training projects
"""
import asyncio
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth import get_current_user
from database import get_supabase
from logger_config import get_logger
from validation import validate_uuid

logger = get_logger(__name__)
router = APIRouter(prefix="/api/outcomes", tags=["outcomes"])
supabase = get_supabase()


# ============================================================================
# Request/Response Models
# ============================================================================

class OutcomeCreateRequest(BaseModel):
    project_id: str
    title: str
    description: Optional[str] = None
    metric_type: str
    baseline_value: Optional[float] = None
    target_value: Optional[float] = None
    unit: Optional[str] = None
    target_date: Optional[str] = None  # ISO date string
    notes: Optional[str] = None
    data_source: Optional[str] = None


class OutcomeUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    baseline_value: Optional[float] = None
    target_value: Optional[float] = None
    actual_value: Optional[float] = None
    unit: Optional[str] = None
    target_date: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    data_source: Optional[str] = None


class OutcomeMeasurementRequest(BaseModel):
    actual_value: float
    notes: Optional[str] = None


# ============================================================================
# Outcome CRUD Operations
# ============================================================================

@router.post("/create")
async def create_outcome(
    request: OutcomeCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a new learning outcome for a project"""
    try:
        validate_uuid(request.project_id, "project_id")
        user_id = current_user['id']

        # Validate metric type
        valid_metric_types = [
            'completion_rate', 'assessment_score', 'performance_improvement',
            'time_to_competency', 'learner_satisfaction', 'knowledge_retention',
            'behavior_change', 'business_impact', 'roi', 'custom'
        ]
        if request.metric_type not in valid_metric_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid metric type. Must be one of: {', '.join(valid_metric_types)}"
            )

        # Verify project belongs to user
        project_result = await asyncio.to_thread(
            lambda: supabase.table('projects')
                .select('id')
                .eq('id', request.project_id)
                .eq('user_id', user_id)
                .single()
                .execute()
        )

        if not project_result.data:
            raise HTTPException(status_code=404, detail="Project not found")

        # Parse target_date if provided
        target_date = None
        if request.target_date:
            try:
                target_date = datetime.fromisoformat(request.target_date.replace('Z', '+00:00')).date().isoformat()
            except ValueError:
                target_date = request.target_date

        # Create outcome
        outcome_data = {
            'project_id': request.project_id,
            'user_id': user_id,
            'title': request.title,
            'description': request.description,
            'metric_type': request.metric_type,
            'baseline_value': request.baseline_value,
            'target_value': request.target_value,
            'unit': request.unit,
            'target_date': target_date,
            'notes': request.notes,
            'data_source': request.data_source,
            'status': 'pending'
        }

        result = await asyncio.to_thread(
            lambda: supabase.table('learning_outcomes')
                .insert(outcome_data)
                .execute()
        )

        logger.info(f"✅ Learning outcome created: {result.data[0]['id']}")

        return {
            'success': True,
            'outcome': result.data[0]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating outcome: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/project/{project_id}")
async def get_project_outcomes(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all outcomes for a project"""
    try:
        validate_uuid(project_id, "project_id")
        user_id = current_user['id']

        # Verify project belongs to user
        project_result = await asyncio.to_thread(
            lambda: supabase.table('projects')
                .select('id, title')
                .eq('id', project_id)
                .eq('user_id', user_id)
                .single()
                .execute()
        )

        if not project_result.data:
            raise HTTPException(status_code=404, detail="Project not found")

        # Get outcomes
        result = await asyncio.to_thread(
            lambda: supabase.table('learning_outcomes')
                .select('*')
                .eq('project_id', project_id)
                .order('created_at', desc=True)
                .execute()
        )

        outcomes = result.data if result.data else []

        # Calculate summary stats
        total = len(outcomes)
        achieved = sum(1 for o in outcomes if o.get('status') == 'achieved')
        in_progress = sum(1 for o in outcomes if o.get('status') == 'in_progress')
        pending = sum(1 for o in outcomes if o.get('status') == 'pending')

        return {
            'success': True,
            'project': project_result.data,
            'outcomes': outcomes,
            'summary': {
                'total': total,
                'achieved': achieved,
                'in_progress': in_progress,
                'pending': pending,
                'achievement_rate': round((achieved / total * 100), 1) if total > 0 else 0
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching outcomes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{outcome_id}")
async def get_outcome(
    outcome_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific outcome"""
    try:
        validate_uuid(outcome_id, "outcome_id")
        user_id = current_user['id']

        result = await asyncio.to_thread(
            lambda: supabase.table('learning_outcomes')
                .select('*, projects(id, title)')
                .eq('id', outcome_id)
                .eq('user_id', user_id)
                .single()
                .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Outcome not found")

        return {
            'success': True,
            'outcome': result.data
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching outcome: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{outcome_id}")
async def update_outcome(
    outcome_id: str,
    request: OutcomeUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update an outcome"""
    try:
        validate_uuid(outcome_id, "outcome_id")
        user_id = current_user['id']

        # Build update data
        update_data = {}
        if request.title is not None:
            update_data['title'] = request.title
        if request.description is not None:
            update_data['description'] = request.description
        if request.baseline_value is not None:
            update_data['baseline_value'] = request.baseline_value
        if request.target_value is not None:
            update_data['target_value'] = request.target_value
        if request.actual_value is not None:
            update_data['actual_value'] = request.actual_value
            update_data['measured_at'] = datetime.utcnow().isoformat()
        if request.unit is not None:
            update_data['unit'] = request.unit
        if request.target_date is not None:
            update_data['target_date'] = request.target_date
        if request.status is not None:
            valid_statuses = ['pending', 'in_progress', 'achieved', 'missed', 'partial']
            if request.status not in valid_statuses:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
                )
            update_data['status'] = request.status
        if request.notes is not None:
            update_data['notes'] = request.notes
        if request.data_source is not None:
            update_data['data_source'] = request.data_source

        if not update_data:
            raise HTTPException(status_code=400, detail="No update data provided")

        result = await asyncio.to_thread(
            lambda: supabase.table('learning_outcomes')
                .update(update_data)
                .eq('id', outcome_id)
                .eq('user_id', user_id)
                .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Outcome not found")

        logger.info(f"✅ Outcome updated: {outcome_id}")

        return {
            'success': True,
            'outcome': result.data[0]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating outcome: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{outcome_id}/measure")
async def record_measurement(
    outcome_id: str,
    request: OutcomeMeasurementRequest,
    current_user: dict = Depends(get_current_user)
):
    """Record an actual measurement for an outcome"""
    try:
        validate_uuid(outcome_id, "outcome_id")
        user_id = current_user['id']

        # Get current outcome to determine status
        current = await asyncio.to_thread(
            lambda: supabase.table('learning_outcomes')
                .select('target_value, baseline_value')
                .eq('id', outcome_id)
                .eq('user_id', user_id)
                .single()
                .execute()
        )

        if not current.data:
            raise HTTPException(status_code=404, detail="Outcome not found")

        # Determine status based on measurement
        target = current.data.get('target_value')
        baseline = current.data.get('baseline_value')
        actual = request.actual_value

        status = 'in_progress'
        if target is not None:
            if actual >= target:
                status = 'achieved'
            elif baseline is not None and actual > baseline:
                status = 'partial'
            elif baseline is not None and actual <= baseline:
                status = 'missed'

        # Update outcome with measurement
        update_data = {
            'actual_value': actual,
            'measured_at': datetime.utcnow().isoformat(),
            'status': status
        }
        if request.notes:
            update_data['notes'] = request.notes

        result = await asyncio.to_thread(
            lambda: supabase.table('learning_outcomes')
                .update(update_data)
                .eq('id', outcome_id)
                .eq('user_id', user_id)
                .execute()
        )

        logger.info(f"✅ Measurement recorded for outcome: {outcome_id}, status: {status}")

        return {
            'success': True,
            'outcome': result.data[0],
            'status': status
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error recording measurement: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{outcome_id}")
async def delete_outcome(
    outcome_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete an outcome"""
    try:
        validate_uuid(outcome_id, "outcome_id")
        user_id = current_user['id']

        result = await asyncio.to_thread(
            lambda: supabase.table('learning_outcomes')
                .delete()
                .eq('id', outcome_id)
                .eq('user_id', user_id)
                .execute()
        )

        logger.info(f"✅ Outcome deleted: {outcome_id}")

        return {
            'success': True,
            'message': 'Outcome deleted successfully'
        }

    except Exception as e:
        logger.error(f"❌ Error deleting outcome: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Analytics and Dashboard
# ============================================================================

@router.get("/dashboard/summary")
async def get_outcomes_dashboard(
    current_user: dict = Depends(get_current_user)
):
    """Get summary dashboard of all user's outcomes across projects"""
    try:
        user_id = current_user['id']

        # Get all outcomes with project info
        result = await asyncio.to_thread(
            lambda: supabase.table('learning_outcomes')
                .select('*, projects(id, title, current_phase)')
                .eq('user_id', user_id)
                .order('created_at', desc=True)
                .execute()
        )

        outcomes = result.data if result.data else []

        # Calculate overall stats
        total = len(outcomes)
        achieved = sum(1 for o in outcomes if o.get('status') == 'achieved')
        in_progress = sum(1 for o in outcomes if o.get('status') == 'in_progress')
        pending = sum(1 for o in outcomes if o.get('status') == 'pending')
        missed = sum(1 for o in outcomes if o.get('status') == 'missed')
        partial = sum(1 for o in outcomes if o.get('status') == 'partial')

        # Group by metric type
        by_metric_type = {}
        for outcome in outcomes:
            mt = outcome.get('metric_type', 'unknown')
            if mt not in by_metric_type:
                by_metric_type[mt] = {'total': 0, 'achieved': 0}
            by_metric_type[mt]['total'] += 1
            if outcome.get('status') == 'achieved':
                by_metric_type[mt]['achieved'] += 1

        # Calculate average progress for in-progress outcomes
        progress_data = []
        for outcome in outcomes:
            baseline = outcome.get('baseline_value')
            target = outcome.get('target_value')
            actual = outcome.get('actual_value')
            if baseline is not None and target is not None and actual is not None and target != baseline:
                progress = ((actual - baseline) / (target - baseline)) * 100
                progress_data.append(min(100, max(0, progress)))

        avg_progress = sum(progress_data) / len(progress_data) if progress_data else 0

        return {
            'success': True,
            'summary': {
                'total_outcomes': total,
                'achieved': achieved,
                'in_progress': in_progress,
                'pending': pending,
                'missed': missed,
                'partial': partial,
                'achievement_rate': round((achieved / total * 100), 1) if total > 0 else 0,
                'average_progress': round(avg_progress, 1)
            },
            'by_metric_type': by_metric_type,
            'recent_outcomes': outcomes[:10]  # Last 10 outcomes
        }

    except Exception as e:
        logger.error(f"❌ Error fetching outcomes dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metric-types")
async def get_metric_types(
    current_user: dict = Depends(get_current_user)
):
    """Get available metric types with descriptions"""
    return {
        'success': True,
        'metric_types': [
            {
                'id': 'completion_rate',
                'name': 'Completion Rate',
                'description': 'Percentage of learners who complete the training',
                'unit': '%',
                'example': 'Target: 95% of enrolled learners complete the course'
            },
            {
                'id': 'assessment_score',
                'name': 'Assessment Score',
                'description': 'Average score on knowledge assessments',
                'unit': '%',
                'example': 'Target: Average score of 80% on final assessment'
            },
            {
                'id': 'performance_improvement',
                'name': 'Performance Improvement',
                'description': 'Measurable improvement in job performance metrics',
                'unit': '%',
                'example': 'Target: 15% increase in sales after training'
            },
            {
                'id': 'time_to_competency',
                'name': 'Time to Competency',
                'description': 'Time required for learners to reach competency',
                'unit': 'days',
                'example': 'Target: Reduce onboarding time from 90 to 60 days'
            },
            {
                'id': 'learner_satisfaction',
                'name': 'Learner Satisfaction',
                'description': 'Learner feedback and satisfaction scores',
                'unit': '/5',
                'example': 'Target: 4.5/5 average satisfaction rating'
            },
            {
                'id': 'knowledge_retention',
                'name': 'Knowledge Retention',
                'description': 'Knowledge retained after a period of time',
                'unit': '%',
                'example': 'Target: 85% retention on 30-day follow-up assessment'
            },
            {
                'id': 'behavior_change',
                'name': 'Behavior Change',
                'description': 'Observable changes in workplace behavior',
                'unit': '%',
                'example': 'Target: 70% of learners apply new skills within 30 days'
            },
            {
                'id': 'business_impact',
                'name': 'Business Impact',
                'description': 'Measurable business outcome improvements',
                'unit': '$',
                'example': 'Target: Reduce errors by 25%, saving $50,000/month'
            },
            {
                'id': 'roi',
                'name': 'Return on Investment',
                'description': 'Financial return compared to training investment',
                'unit': '%',
                'example': 'Target: 200% ROI within 12 months'
            },
            {
                'id': 'custom',
                'name': 'Custom Metric',
                'description': 'Define your own metric and measurement criteria',
                'unit': 'varies',
                'example': 'Any metric specific to your training goals'
            }
        ]
    }
