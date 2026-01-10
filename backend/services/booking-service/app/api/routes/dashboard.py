from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Any

from app.core.database import get_db
from app.services.dashboard_service import DashboardService
from app.api.deps import get_current_user_id

router = APIRouter()

async def get_dashboard_service(db: AsyncSession = Depends(get_db)) -> DashboardService:
    return DashboardService(db)

@router.get("/driver", response_model=Any)
async def get_driver_dashboard(
    current_user_id: UUID = Depends(get_current_user_id),
    service: DashboardService = Depends(get_dashboard_service)
):
    """
    Get dashboard statistics for the current driver.
    """
    return await service.get_driver_dashboard(current_user_id)
