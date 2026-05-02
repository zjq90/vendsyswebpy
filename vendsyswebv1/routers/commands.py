"""
远程控制命令路由
处理设备远程控制操作
包括：远程重启、远程开锁、调整温度、设置广告、固件升级
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime
import json

from database import get_db
from models import CommandLog, Device, Firmware, User, HardwareParams
from schemas import CommandCreate, CommandResponse, BatchCommandCreate
from routers.auth import get_current_user, get_current_admin

router = APIRouter(prefix="/api/commands", tags=["远程控制"])


def create_command_log(
    db: Session,
    device_id: int,
    user_id: int,
    command_type: str,
    command_name: str,
    command_params: dict = None
):
    """
    创建命令日志记录
    """
    command = CommandLog(
        device_id=device_id,
        user_id=user_id,
        command_type=command_type,
        command_name=command_name,
        command_params=json.dumps(command_params) if command_params else None,
        status="pending"
    )
    db.add(command)
    db.commit()
    db.refresh(command)
    return command


def mock_execute_command(command: CommandLog, db: Session):
    """
    模拟执行命令
    在真实环境中，这里会调用真实的设备通信接口
    """
    command.status = "sent"
    command.sent_at = datetime.now()
    db.commit()

    # 模拟执行延迟
    import time
    time.sleep(0.5)

    # 90%概率成功
    import random
    success = random.random() < 0.9

    if success:
        command.status = "success"
        command.executed_at = datetime.now()
        command.completed_at = datetime.now()
        command.result_message = f"命令执行成功"

        # 根据命令类型执行相应的模拟操作
        if command.command_type == "reboot":
            command.result_message = "设备重启成功"
        elif command.command_type == "unlock":
            command.result_message = "门锁已解锁"
            # 更新硬件参数中的门锁状态
            hw = db.query(HardwareParams).filter(
                HardwareParams.device_id == command.device_id
            ).order_by(desc(HardwareParams.recorded_at)).first()
            if hw:
                hw.door_lock_status = "unlocked"
                db.commit()
        elif command.command_type == "set_temp":
            command.result_message = "温度设置成功"
        elif command.command_type == "set_ad":
            command.result_message = "广告内容设置成功"
        elif command.command_type == "firmware_upgrade":
            command.result_message = "固件升级成功"
            command.upgrade_progress = 100
    else:
        command.status = "failed"
        command.executed_at = datetime.now()
        command.completed_at = datetime.now()
        command.result_message = "命令执行失败：设备响应超时"

    db.commit()
    return command


@router.post("/reboot/{device_id}", response_model=CommandResponse)
def reboot_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    远程重启设备
    需要管理员权限
    """
    # 检查设备是否存在
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    # 创建命令记录
    command = create_command_log(
        db, device_id, current_user.id,
        "reboot", "远程重启设备"
    )

    # 模拟执行
    command = mock_execute_command(command, db)

    return command


@router.post("/unlock/{device_id}", response_model=CommandResponse)
def unlock_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    远程开锁
    需要管理员权限
    """
    # 检查设备是否存在
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    # 创建命令记录
    command = create_command_log(
        db, device_id, current_user.id,
        "unlock", "远程开锁"
    )

    # 模拟执行
    command = mock_execute_command(command, db)

    return command


@router.post("/set-temperature/{device_id}", response_model=CommandResponse)
def set_device_temperature(
    device_id: int,
    target_temp: float = Query(..., ge=-20, le=50, description="目标温度"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    调整制冷/加热温度
    需要管理员权限
    """
    # 检查设备是否存在
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    # 创建命令记录
    command = create_command_log(
        db, device_id, current_user.id,
        "set_temp", f"设置温度为{target_temp}°C",
        {"target_temperature": target_temp}
    )

    # 模拟执行并更新硬件参数
    command = mock_execute_command(command, db)

    if command.status == "success":
        # 更新最新硬件参数中的目标温度
        hw = db.query(HardwareParams).filter(
            HardwareParams.device_id == device_id
        ).order_by(desc(HardwareParams.recorded_at)).first()
        if hw:
            hw.target_temperature = target_temp
            db.commit()

    return command


@router.post("/set-ad/{device_id}", response_model=CommandResponse)
def set_device_ad_content(
    device_id: int,
    ad_content: str = Query(..., max_length=500, description="广告内容"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    设置屏幕广告内容
    需要管理员权限
    """
    # 检查设备是否存在
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    # 创建命令记录
    command = create_command_log(
        db, device_id, current_user.id,
        "set_ad", "设置广告内容",
        {"ad_content": ad_content}
    )

    # 模拟执行并更新硬件参数
    command = mock_execute_command(command, db)

    if command.status == "success":
        # 更新最新硬件参数中的广告内容
        hw = db.query(HardwareParams).filter(
            HardwareParams.device_id == device_id
        ).order_by(desc(HardwareParams.recorded_at)).first()
        if hw:
            hw.current_ad_content = ad_content
            db.commit()

    return command


@router.post("/firmware-upgrade/{device_id}", response_model=CommandResponse)
def firmware_upgrade(
    device_id: int,
    firmware_id: int = Query(..., description="固件ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    设备固件升级
    需要管理员权限
    """
    # 检查设备是否存在
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    # 检查固件是否存在
    firmware = db.query(Firmware).filter(Firmware.id == firmware_id).first()
    if not firmware:
        raise HTTPException(status_code=404, detail="固件不存在")

    # 创建命令记录
    command = create_command_log(
        db, device_id, current_user.id,
        "firmware_upgrade", f"升级固件到版本 {firmware.version}",
        {"firmware_id": firmware_id, "version": firmware.version}
    )
    command.firmware_id = firmware_id
    command.firmware_version = firmware.version
    db.commit()

    # 模拟执行
    command = mock_execute_command(command, db)

    if command.status == "success":
        # 更新设备的固件版本
        device.firmware_version = firmware.version
        firmware.update_success_count += 1
        db.commit()

    return command


@router.post("/batch/reboot", response_model=List[CommandResponse])
def batch_reboot_devices(
    batch_data: BatchCommandCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    批量重启设备
    需要管理员权限
    """
    results = []
    for device_id in batch_data.device_ids:
        try:
            # 检查设备是否存在
            device = db.query(Device).filter(Device.id == device_id).first()
            if not device:
                continue

            # 创建命令记录
            command = create_command_log(
                db, device_id, current_user.id,
                "reboot", "批量远程重启设备"
            )
            # 模拟执行
            command = mock_execute_command(command, db)
            results.append(command)
        except Exception as e:
            print(f"设备 {device_id} 重启失败: {e}")

    return results


@router.get("/history/device/{device_id}", response_model=List[CommandResponse])
def get_device_command_history(
    device_id: int,
    limit: int = Query(50, ge=1, le=500),
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取设备命令历史
    """
    # 检查设备是否存在
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    query = db.query(CommandLog).filter(CommandLog.device_id == device_id)

    if status:
        query = query.filter(CommandLog.status == status)

    commands = query.order_by(desc(CommandLog.created_at)).limit(limit).all()
    return commands


@router.get("/stats/summary")
def get_command_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取命令执行统计
    """
    from sqlalchemy import func, case

    # 按状态统计
    status_stats = db.query(
        CommandLog.status,
        func.count(CommandLog.id).label('count')
    ).group_by(CommandLog.status).all()

    # 按命令类型统计
    type_stats = db.query(
        CommandLog.command_type,
        func.count(CommandLog.id).label('count')
    ).group_by(CommandLog.command_type).all()

    return {
        "by_status": [{"status": s[0], "count": s[1]} for s in status_stats],
        "by_type": [{"type": t[0], "count": t[1]} for t in type_stats]
    }
