"""
设备管理路由
处理设备的增删改查操作
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional

from database import get_db
from models import Device, DeviceStatus, User
from schemas import DeviceCreate, DeviceResponse, DeviceUpdate
from routers.auth import get_current_user, get_current_admin

router = APIRouter(prefix="/api/devices", tags=["设备管理"])


@router.get("/", response_model=List[DeviceResponse])
def get_devices(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    device_code: Optional[str] = None,
    status: Optional[str] = None,
    is_online: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取设备列表
    支持分页、设备编号搜索、状态筛选
    """
    query = db.query(Device)

    # 搜索筛选
    if device_code:
        query = query.filter(Device.device_code.contains(device_code))
    if status:
        query = query.filter(Device.status == status)

    # 排序
    query = query.order_by(desc(Device.created_at))

    # 分页
    devices = query.offset(skip).limit(limit).all()

    # 补充最新状态信息
    for device in devices:
        last_status = db.query(DeviceStatus).filter(
            DeviceStatus.device_id == device.id
        ).order_by(desc(DeviceStatus.recorded_at)).first()
        if last_status:
            device.last_status = last_status
        else:
            device.last_status = None

    return devices


@router.get("/{device_id}", response_model=DeviceResponse)
def get_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取单个设备详情
    """
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    # 补充最新状态
    last_status = db.query(DeviceStatus).filter(
        DeviceStatus.device_id == device.id
    ).order_by(desc(DeviceStatus.recorded_at)).first()
    device.last_status = last_status

    return device


@router.post("/", response_model=DeviceResponse)
def create_device(
    device_data: DeviceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    创建设备
    需要管理员权限
    """
    # 检查设备编号是否已存在
    existing_device = db.query(Device).filter(Device.device_code == device_data.device_code).first()
    if existing_device:
        raise HTTPException(status_code=400, detail="设备编号已存在")

    new_device = Device(**device_data.dict())
    db.add(new_device)
    db.commit()
    db.refresh(new_device)
    return new_device


@router.put("/{device_id}", response_model=DeviceResponse)
def update_device(
    device_id: int,
    device_data: DeviceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    更新设备信息
    需要管理员权限
    """
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    # 更新字段
    update_data = device_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(device, key, value)

    db.commit()
    db.refresh(device)
    return device


@router.delete("/{device_id}")
def delete_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    删除设备
    需要管理员权限
    """
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    db.delete(device)
    db.commit()
    return {"message": "设备删除成功", "device_id": device_id}


@router.get("/count/summary")
def get_device_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取设备统计概览
    在线数量、离线数量、故障数量等
    """
    total = db.query(Device).count()

    # 获取最新状态
    from sqlalchemy import func
    latest_status_subquery = db.query(
        DeviceStatus.device_id,
        func.max(DeviceStatus.recorded_at).label('latest_time')
    ).group_by(DeviceStatus.device_id).subquery()

    latest_status = db.query(DeviceStatus).join(
        latest_status_subquery,
        (DeviceStatus.device_id == latest_status_subquery.c.device_id) &
        (DeviceStatus.recorded_at == latest_status_subquery.c.latest_time)
    ).all()

    online_count = sum(1 for s in latest_status if s.is_online)
    offline_count = total - online_count

    # 故障设备
    fault_count = db.query(Device).filter(Device.status == "faulty").count()
    maintenance_count = db.query(Device).filter(Device.status == "maintenance").count()

    return {
        "total": total,
        "online": online_count,
        "offline": offline_count,
        "faulty": fault_count,
        "maintenance": maintenance_count,
        "normal": total - fault_count - maintenance_count
    }
