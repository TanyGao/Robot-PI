from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from src.common.database import get_async_session, Device

router = APIRouter(prefix="/devices")

class DeviceCreate(BaseModel):
    name: str
    status: str = "online"
    device_type: str = "raspberry_pi"

class DeviceStatus(BaseModel):
    status: str

@router.post("/register")
async def register_device(
    device: DeviceCreate,
    session: AsyncSession = Depends(get_async_session)
):
    new_device = Device(
        name=device.name,
        device_type=device.device_type,
        status=device.status,
        last_seen=datetime.utcnow()
    )
    session.add(new_device)
    await session.commit()
    await session.refresh(new_device)
    return new_device

@router.post("/{device_id}/status")
async def update_device_status(
    device_id: int,
    status: DeviceStatus,
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(
        select(Device).where(Device.id == device_id)
    )
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
        
    device.status = status.status
    device.last_seen = datetime.utcnow()
    await session.commit()
    await session.refresh(device)
    return device