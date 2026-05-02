"""
设备状态监控路由
处理设备状态和硬件参数的查询、模拟更新
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime, timedelta

from database import get_db
from models import DeviceStatus, HardwareParams, Device, User
from schemas import DeviceStatusResponse, HardwareParamsResponse
from routers.auth import get_current_user
from utils.mock_device import mock_device_status_update, mock_hardware_params_update

router = APIRouter(prefix="/api/status", tags=["状态监控"])


@router.get("/device/{device_id}/latest", response_model=DeviceStatusResponse)
def get_latest_device_status(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取设备最新状态
    """
    # 检查设备是否存在
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    status = db.query(DeviceStatus).filter(
        DeviceStatus.device_id == device_id
    ).order_by(desc(DeviceStatus.recorded_at)).first()

    if not status:
        raise HTTPException(status_code=404, detail="暂无设备状态数据")
    return status


@router.get("/device/{device_id}/history", response_model=List[DeviceStatusResponse])
def get_device_status_history(
    device_id: int,
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取设备状态历史
    默认查询最近24小时的数据
    """
    # 检查设备是否存在
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    time_threshold = datetime.now() - timedelta(hours=hours)
    statuses = db.query(DeviceStatus).filter(
        DeviceStatus.device_id == device_id,
        DeviceStatus.recorded_at >= time_threshold
    ).order_by(desc(DeviceStatus.recorded_at)).limit(limit).all()
    return statuses


@router.get("/hardware/{device_id}/latest", response_model=HardwareParamsResponse)
def get_latest_hardware_params(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取设备最新硬件参数
    """
    # 检查设备是否存在
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    params = db.query(HardwareParams).filter(
        HardwareParams.device_id == device_id
    ).order_by(desc(HardwareParams.recorded_at)).first()

    if not params:
        raise HTTPException(status_code=404, detail="暂无硬件参数数据")
    return params


@router.get("/hardware/{device_id}/history", response_model=List[HardwareParamsResponse])
def get_hardware_params_history(
    device_id: int,
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取硬件参数历史
    默认查询最近24小时的数据
    """
    # 检查设备是否存在
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    time_threshold = datetime.now() - timedelta(hours=hours)
    params = db.query(HardwareParams).filter(
        HardwareParams.device_id == device_id,
        HardwareParams.recorded_at >= time_threshold
    ).order_by(desc(HardwareParams.recorded_at)).limit(limit).all()
    return params


@router.post("/mock/update/{device_id}")
def mock_update_device_status(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    模拟设备状态更新
    生成随机的设备状态和硬件参数数据用于测试
    """
    # 检查设备是否存在
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    # 生成模拟状态数据
    status_data = mock_device_status_update(device_id)
    new_status = DeviceStatus(**status_data)
    db.add(new_status)

    # 生成模拟硬件参数数据
    hardware_data = mock_hardware_params_update(device_id)
    new_hardware = HardwareParams(**hardware_data)
    db.add(new_hardware)

    db.commit()

    return {
        "message": "模拟数据生成成功",
        "device_id": device_id,
        "status": {
            "is_online": status_data["is_online"],
            "signal_strength": status_data["signal_strength"],
            "signal_level": status_data["signal_level"]
        },
        "hardware": {
            "temperature": hardware_data["temperature"],
            "humidity": hardware_data["humidity"],
            "door_lock_status": hardware_data["door_lock_status"],
            "has_fault": hardware_data["has_fault"]
        }
    }


@router.post("/mock/update-all")
def mock_update_all_devices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    模拟所有设备状态更新
    为所有设备生成模拟数据
    """
    devices = db.query(Device).all()
    updated_count = 0

    for device in devices:
        try:
            # 生成模拟状态数据
            status_data = mock_device_status_update(device.id)
            new_status = DeviceStatus(**status_data)
            db.add(new_status)

            # 生成模拟硬件参数数据
            hardware_data = mock_hardware_params_update(device.id)
            new_hardware = HardwareParams(**hardware_data)
            db.add(new_hardware)

            updated_count += 1
        except Exception as e:
            print(f"设备 {device.id} 更新失败: {e}")

    db.commit()

    return {
        "message": "批量模拟数据生成完成",
        "total_devices": len(devices),
        "updated_count": updated_count
    }


@router.get("/overview")
def get_status_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取所有设备状态概览
    用于监控大屏展示
    """
    from sqlalchemy import func

    # 统计数据
    total_devices = db.query(Device).count()

    # 最新状态统计
    latest_status_subquery = db.query(
        DeviceStatus.device_id,
        func.max(DeviceStatus.recorded_at).label('latest_time')
    ).group_by(DeviceStatus.device_id).subquery()

    latest_statuses = db.query(DeviceStatus).join(
        latest_status_subquery,
        (DeviceStatus.device_id == latest_status_subquery.c.device_id) &
        (DeviceStatus.recorded_at == latest_status_subquery.c.latest_time)
    ).all()

    # 统计在线/离线
    online_count = sum(1 for s in latest_statuses if s.is_online)
    offline_count = total_devices - online_count

    # 统计信号等级分布
    signal_distribution = {
        "excellent": 0,
        "good": 0,
        "fair": 0,
        "poor": 0,
        "no_data": 0
    }
    for s in latest_statuses:
        if s.signal_level in signal_distribution:
            signal_distribution[s.signal_level] += 1
        else:
            signal_distribution["no_data"] += 1

    # 最新硬件参数统计
    latest_hardware_subquery = db.query(
        HardwareParams.device_id,
        func.max(HardwareParams.recorded_at).label('latest_time')
    ).group_by(HardwareParams.device_id).subquery()

    latest_hardware = db.query(HardwareParams).join(
        latest_hardware_subquery,
        (HardwareParams.device_id == latest_hardware_subquery.c.device_id) &
        (HardwareParams.recorded_at == latest_hardware_subquery.c.latest_time)
    ).all()

    # 故障统计
    fault_count = sum(1 for h in latest_hardware if h.has_fault)
    door_fault_count = sum(1 for h in latest_hardware if h.door_lock_status == "fault")
    motor_fault_count = sum(1 for h in latest_hardware if h.motor_fault_count > 0)

    # 温度统计
    temps = [h.temperature for h in latest_hardware if h.temperature is not None]
    avg_temperature = round(sum(temps) / len(temps), 1) if temps else 0

    return {
        "devices": {
            "total": total_devices,
            "online": online_count,
            "offline": offline_count
        },
        "signal_distribution": signal_distribution,
        "hardware": {
            "total_faults": fault_count,
            "door_faults": door_fault_count,
            "motor_faults": motor_fault_count,
            "avg_temperature": avg_temperature
        }
    }
