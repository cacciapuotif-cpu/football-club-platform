"""
Training Plans Router - Complete CRUD operations and plan generation.
"""

import logging
from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.plan import PlanAdherence, PlanTask, TaskStatus, TrainingArea, TrainingPlan
from app.models.player import Player
from app.schemas.plan import (
    PlanAdherenceCreate,
    PlanAdherenceResponse,
    PlanAdherenceStatsResponse,
    PlanAdherenceUpdate,
    PlanGenerationRequest,
    PlanTaskCreate,
    PlanTaskResponse,
    PlanTaskUpdate,
    PlayerPlanHistoryResponse,
    TrainingPlanCreate,
    TrainingPlanListResponse,
    TrainingPlanResponse,
    TrainingPlanUpdate,
    TrainingPlanWithTasks,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================
# TRAINING PLANS CRUD ENDPOINTS
# ============================================


@router.get("/", response_model=TrainingPlanListResponse, status_code=status.HTTP_200_OK)
async def list_training_plans(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    player_id: Optional[UUID] = Query(None, description="Filter by player"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    from_date: Optional[date] = Query(None, description="Filter from week start date"),
    to_date: Optional[date] = Query(None, description="Filter to week start date"),
    organization_id: Optional[UUID] = Query(None, description="Filter by organization"),
    session: AsyncSession = Depends(get_session),
):
    """
    List all training plans with pagination and filters.

    - **page**: Page number (starts at 1)
    - **page_size**: Number of items per page (max 100)
    - **player_id**: Filter by player
    - **is_active**: Filter by active status
    - **from_date**: Filter plans starting from this date
    - **to_date**: Filter plans starting before this date
    - **organization_id**: Filter by organization (multi-tenant)
    """
    try:
        # Build query
        query = select(TrainingPlan)

        # Apply filters
        if player_id:
            query = query.where(TrainingPlan.player_id == player_id)
        if is_active is not None:
            query = query.where(TrainingPlan.is_active == is_active)
        if from_date:
            query = query.where(TrainingPlan.week_start >= from_date)
        if to_date:
            query = query.where(TrainingPlan.week_start <= to_date)
        if organization_id:
            query = query.where(TrainingPlan.organization_id == organization_id)

        # Count total items
        count_query = select(func.count()).select_from(query.subquery())
        total = await session.scalar(count_query)

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(TrainingPlan.week_start.desc())

        # Execute query
        result = await session.execute(query)
        plans = result.scalars().all()

        # Calculate pages
        pages = (total + page_size - 1) // page_size if total > 0 else 0

        return TrainingPlanListResponse(
            plans=[TrainingPlanResponse.model_validate(plan) for plan in plans],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    except Exception as e:
        logger.error(f"Error listing training plans: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list training plans: {str(e)}",
        )


@router.get("/{plan_id}", response_model=TrainingPlanWithTasks, status_code=status.HTTP_200_OK)
async def get_training_plan(
    plan_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """
    Get a specific training plan by ID with tasks summary.

    - **plan_id**: The training plan UUID
    """
    try:
        # Get plan
        result = await session.execute(select(TrainingPlan).where(TrainingPlan.id == plan_id))
        plan = result.scalar_one_or_none()

        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Training plan with id {plan_id} not found",
            )

        # Get tasks stats
        tasks_result = await session.execute(
            select(
                func.count(PlanTask.id).label("total_tasks"),
                func.sum(
                    func.case((PlanTask.status == TaskStatus.COMPLETED, 1), else_=0)
                ).label("completed_tasks"),
                func.avg(PlanTask.completion_pct).label("avg_completion"),
            ).where(PlanTask.plan_id == plan_id)
        )
        tasks_stats = tasks_result.one()

        total_tasks = tasks_stats.total_tasks or 0
        completed_tasks = tasks_stats.completed_tasks or 0
        avg_completion = tasks_stats.avg_completion or 0.0

        # Build response
        plan_dict = TrainingPlanResponse.model_validate(plan).model_dump()
        plan_dict["tasks_count"] = total_tasks
        plan_dict["completed_tasks"] = completed_tasks
        plan_dict["adherence_pct"] = round(avg_completion, 2)

        return TrainingPlanWithTasks(**plan_dict)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting training plan {plan_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get training plan: {str(e)}",
        )


@router.post("/", response_model=TrainingPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_training_plan(
    plan_data: TrainingPlanCreate,
    session: AsyncSession = Depends(get_session),
):
    """
    Create a new training plan.

    - **player_id**: Player ID (required)
    - **week_start**: Week start date (required)
    - **week_end**: Week end date (required)
    - **target_areas**: Target training areas (optional)
    - **organization_id**: Organization ID (required)
    """
    try:
        # Validate player exists
        player_result = await session.execute(
            select(Player).where(Player.id == plan_data.player_id)
        )
        player = player_result.scalar_one_or_none()

        if not player:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Player with id {plan_data.player_id} not found",
            )

        # Validate dates
        if plan_data.week_end <= plan_data.week_start:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Week end date must be after week start date",
            )

        # Create plan
        plan = TrainingPlan(**plan_data.model_dump())

        session.add(plan)
        await session.commit()
        await session.refresh(plan)

        logger.info(
            f"Created training plan for player {player.first_name} {player.last_name} (id={plan.id})"
        )

        return TrainingPlanResponse.model_validate(plan)

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error creating training plan: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create training plan: {str(e)}",
        )


@router.put("/{plan_id}", response_model=TrainingPlanResponse, status_code=status.HTTP_200_OK)
async def update_training_plan(
    plan_id: UUID,
    plan_data: TrainingPlanUpdate,
    session: AsyncSession = Depends(get_session),
):
    """
    Update an existing training plan.

    - **plan_id**: The training plan UUID
    - All fields are optional
    """
    try:
        # Get plan
        result = await session.execute(select(TrainingPlan).where(TrainingPlan.id == plan_id))
        plan = result.scalar_one_or_none()

        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Training plan with id {plan_id} not found",
            )

        # Update plan fields
        update_data = plan_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(plan, key, value)

        # Validate dates if both are set
        if plan.week_end <= plan.week_start:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Week end date must be after week start date",
            )

        await session.commit()
        await session.refresh(plan)

        logger.info(f"Updated training plan: {plan.id}")

        return TrainingPlanResponse.model_validate(plan)

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error updating training plan {plan_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update training plan: {str(e)}",
        )


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_training_plan(
    plan_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """
    Delete a training plan.

    - **plan_id**: The training plan UUID

    **Note**: This will also delete all tasks and adherence records for this plan.
    """
    try:
        # Get plan
        result = await session.execute(select(TrainingPlan).where(TrainingPlan.id == plan_id))
        plan = result.scalar_one_or_none()

        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Training plan with id {plan_id} not found",
            )

        # Delete plan (cascade will delete tasks and adherences)
        await session.delete(plan)
        await session.commit()

        logger.info(f"Deleted training plan: {plan.id}")

        return None

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error deleting training plan {plan_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete training plan: {str(e)}",
        )


# ============================================
# PLAN TASKS CRUD ENDPOINTS
# ============================================


@router.get("/{plan_id}/tasks", response_model=list[PlanTaskResponse], status_code=status.HTTP_200_OK)
async def list_plan_tasks(
    plan_id: UUID,
    area: Optional[TrainingArea] = Query(None, description="Filter by training area"),
    status_filter: Optional[TaskStatus] = Query(None, description="Filter by status"),
    session: AsyncSession = Depends(get_session),
):
    """
    List all tasks for a training plan.

    - **plan_id**: The training plan UUID
    - **area**: Filter by training area
    - **status_filter**: Filter by task status
    """
    try:
        # Verify plan exists
        plan_result = await session.execute(select(TrainingPlan).where(TrainingPlan.id == plan_id))
        plan = plan_result.scalar_one_or_none()

        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Training plan with id {plan_id} not found",
            )

        # Get tasks
        query = select(PlanTask).where(PlanTask.plan_id == plan_id)

        if area:
            query = query.where(PlanTask.area == area)
        if status_filter:
            query = query.where(PlanTask.status == status_filter)

        query = query.order_by(
            PlanTask.scheduled_date.asc().nullslast(),
            PlanTask.priority.desc(),
            PlanTask.created_at.asc(),
        )

        result = await session.execute(query)
        tasks = result.scalars().all()

        return [PlanTaskResponse.model_validate(task) for task in tasks]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing plan tasks for plan {plan_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list plan tasks: {str(e)}",
        )


@router.post("/tasks", response_model=PlanTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_plan_task(
    task_data: PlanTaskCreate,
    session: AsyncSession = Depends(get_session),
):
    """
    Create a new plan task.

    - **plan_id**: Training plan ID (required)
    - **area**: Training area (required)
    - **title**: Task title (required)
    - **description**: Task description (optional)
    - **target_metric**: Target metric (optional)
    - **target_value**: Target value (optional)
    - **scheduled_date**: Scheduled date (optional)
    - **priority**: Priority 1-5 (default: 3)
    """
    try:
        # Validate plan exists
        plan_result = await session.execute(
            select(TrainingPlan).where(TrainingPlan.id == task_data.plan_id)
        )
        plan = plan_result.scalar_one_or_none()

        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Training plan with id {task_data.plan_id} not found",
            )

        # Create task
        task = PlanTask(**task_data.model_dump())

        session.add(task)
        await session.commit()
        await session.refresh(task)

        logger.info(f"Created plan task: {task.title} (id={task.id})")

        return PlanTaskResponse.model_validate(task)

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error creating plan task: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create plan task: {str(e)}",
        )


@router.put("/tasks/{task_id}", response_model=PlanTaskResponse, status_code=status.HTTP_200_OK)
async def update_plan_task(
    task_id: UUID,
    task_data: PlanTaskUpdate,
    session: AsyncSession = Depends(get_session),
):
    """
    Update a plan task.

    - **task_id**: The plan task UUID
    - All fields are optional
    """
    try:
        # Get task
        result = await session.execute(select(PlanTask).where(PlanTask.id == task_id))
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plan task with id {task_id} not found",
            )

        # Update task fields
        update_data = task_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(task, key, value)

        await session.commit()
        await session.refresh(task)

        logger.info(f"Updated plan task: {task.title} (id={task.id})")

        return PlanTaskResponse.model_validate(task)

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error updating plan task {task_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update plan task: {str(e)}",
        )


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan_task(
    task_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """
    Delete a plan task.

    - **task_id**: The plan task UUID
    """
    try:
        # Get task
        result = await session.execute(select(PlanTask).where(PlanTask.id == task_id))
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plan task with id {task_id} not found",
            )

        # Delete task
        await session.delete(task)
        await session.commit()

        logger.info(f"Deleted plan task: {task.id}")

        return None

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error deleting plan task {task_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete plan task: {str(e)}",
        )


# ============================================
# PLAN ADHERENCE ENDPOINTS
# ============================================


@router.post("/adherence", response_model=PlanAdherenceResponse, status_code=status.HTTP_201_CREATED)
async def create_adherence(
    adherence_data: PlanAdherenceCreate,
    session: AsyncSession = Depends(get_session),
):
    """
    Record adherence for a plan task.

    - **task_id**: Plan task ID (required)
    - **player_id**: Player ID (required)
    - **completed_date**: Completion date (required)
    - **status**: Task status (COMPLETED, PARTIAL, SKIPPED) (required)
    - **actual_value**: Actual value achieved (optional)
    - **notes**: Additional notes (optional)
    """
    try:
        # Validate task exists
        task_result = await session.execute(
            select(PlanTask).where(PlanTask.id == adherence_data.task_id)
        )
        task = task_result.scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plan task with id {adherence_data.task_id} not found",
            )

        # Create adherence
        adherence = PlanAdherence(**adherence_data.model_dump())

        session.add(adherence)

        # Update task status and completion
        if adherence_data.status == TaskStatus.COMPLETED:
            task.status = TaskStatus.COMPLETED
            task.completion_pct = 100.0
        elif adherence_data.status == TaskStatus.PARTIAL:
            task.status = TaskStatus.PARTIAL
            # Calculate completion based on actual vs target
            if task.target_value and adherence_data.actual_value:
                task.completion_pct = min(
                    100.0, (adherence_data.actual_value / task.target_value) * 100
                )
        elif adherence_data.status == TaskStatus.SKIPPED:
            task.status = TaskStatus.SKIPPED
            task.completion_pct = 0.0

        await session.commit()
        await session.refresh(adherence)

        logger.info(f"Created adherence for task {task.title}: {adherence_data.status}")

        return PlanAdherenceResponse.model_validate(adherence)

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error creating adherence: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create adherence: {str(e)}",
        )


# ============================================
# PLAN GENERATION ENDPOINT
# ============================================


@router.post("/generate", response_model=TrainingPlanResponse, status_code=status.HTTP_201_CREATED)
async def generate_training_plan(
    generation_request: PlanGenerationRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Generate a new training plan for a player.

    This endpoint creates a basic training plan with default tasks.
    In the future, this will integrate with ML models for personalized plan generation.

    - **player_id**: Player ID (required)
    - **week_start**: Week start date (required)
    - **week_end**: Week end date (required)
    - **target_areas**: Target training areas (required)
    - **use_ml**: Use ML for generation (not yet implemented)
    """
    try:
        # Validate player exists
        player_result = await session.execute(
            select(Player).where(Player.id == generation_request.player_id)
        )
        player = player_result.scalar_one_or_none()

        if not player:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Player with id {generation_request.player_id} not found",
            )

        # Create plan
        plan = TrainingPlan(
            player_id=generation_request.player_id,
            week_start=generation_request.week_start,
            week_end=generation_request.week_end,
            target_areas=[area.value for area in generation_request.target_areas],
            organization_id=generation_request.organization_id,
            generated_by="rules" if not generation_request.use_ml else "ml",
            is_active=True,
        )

        session.add(plan)
        await session.flush()  # Get plan ID

        # Generate basic tasks for each target area (rule-based for now)
        for area in generation_request.target_areas:
            task = PlanTask(
                plan_id=plan.id,
                area=area,
                title=f"{area.value} - Weekly Goal",
                description=f"Focus on {area.value} development this week",
                priority=3,
                organization_id=generation_request.organization_id,
            )
            session.add(task)

        await session.commit()
        await session.refresh(plan)

        logger.info(f"Generated training plan for player {player.first_name} {player.last_name}")

        return TrainingPlanResponse.model_validate(plan)

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error generating training plan: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate training plan: {str(e)}",
        )


# ============================================
# PLAN STATISTICS ENDPOINTS
# ============================================


@router.get("/{plan_id}/adherence", response_model=PlanAdherenceStatsResponse, status_code=status.HTTP_200_OK)
async def get_plan_adherence_stats(
    plan_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """
    Get adherence statistics for a training plan.

    Returns:
    - Task completion counts by status
    - Overall adherence percentage
    - Adherence breakdown by training area
    """
    try:
        # Get plan
        plan_result = await session.execute(select(TrainingPlan).where(TrainingPlan.id == plan_id))
        plan = plan_result.scalar_one_or_none()

        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Training plan with id {plan_id} not found",
            )

        # Get task stats
        tasks_query = select(
            func.count(PlanTask.id).label("total"),
            func.sum(func.case((PlanTask.status == TaskStatus.COMPLETED, 1), else_=0)).label("completed"),
            func.sum(func.case((PlanTask.status == TaskStatus.PARTIAL, 1), else_=0)).label("partial"),
            func.sum(func.case((PlanTask.status == TaskStatus.PENDING, 1), else_=0)).label("pending"),
            func.sum(func.case((PlanTask.status == TaskStatus.SKIPPED, 1), else_=0)).label("skipped"),
            func.avg(PlanTask.completion_pct).label("avg_completion"),
        ).where(PlanTask.plan_id == plan_id)

        stats_result = await session.execute(tasks_query)
        stats = stats_result.one()

        # Get adherence by area
        area_query = (
            select(PlanTask.area, func.avg(PlanTask.completion_pct).label("avg_adherence"))
            .where(PlanTask.plan_id == plan_id)
            .group_by(PlanTask.area)
        )

        area_result = await session.execute(area_query)
        area_stats = area_result.all()

        adherence_by_area = {area: round(avg, 2) for area, avg in area_stats}

        return PlanAdherenceStatsResponse(
            plan_id=plan.id,
            player_id=plan.player_id,
            week_start=plan.week_start,
            week_end=plan.week_end,
            total_tasks=stats.total or 0,
            completed_tasks=stats.completed or 0,
            partial_tasks=stats.partial or 0,
            pending_tasks=stats.pending or 0,
            skipped_tasks=stats.skipped or 0,
            overall_adherence_pct=round(stats.avg_completion or 0.0, 2),
            avg_completion_pct=round(stats.avg_completion or 0.0, 2),
            adherence_by_area=adherence_by_area,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting plan adherence stats for plan {plan_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get plan adherence stats: {str(e)}",
        )
