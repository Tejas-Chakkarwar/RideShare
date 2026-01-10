from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID

from app.core.database import get_db
from app.api.deps import get_current_user_id
from app.models.ride_template import RideTemplate
from app.schemas.ride_template import RideTemplateCreate, RideTemplateResponse, RideTemplateUpdate

router = APIRouter()

@router.post("/", response_model=RideTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_ride_template(
    template_in: RideTemplateCreate,
    driver_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new ride template.
    """
    template = RideTemplate(
        **template_in.dict(),
        driver_id=driver_id
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return template

@router.get("/", response_model=List[RideTemplateResponse])
async def list_ride_templates(
    driver_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List all templates for the current driver.
    """
    query = select(RideTemplate).where(RideTemplate.driver_id == driver_id).order_by(RideTemplate.created_at.desc())
    result = await db.execute(query)
    templates = result.scalars().all()
    return templates

@router.get("/{template_id}", response_model=RideTemplateResponse)
async def get_ride_template(
    template_id: UUID,
    driver_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a specific template.
    """
    query = select(RideTemplate).where(
        RideTemplate.id == template_id,
        RideTemplate.driver_id == driver_id
    )
    result = await db.execute(query)
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
        
    return template

@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ride_template(
    template_id: UUID,
    driver_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a template.
    """
    query = select(RideTemplate).where(
        RideTemplate.id == template_id,
        RideTemplate.driver_id == driver_id
    )
    result = await db.execute(query)
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
        
    await db.delete(template)
    await db.commit()
    return None
