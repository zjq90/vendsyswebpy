from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models import VendingMachine, Aisle
from app.schemas import (
    VendingMachineCreate,
    VendingMachineUpdate,
    VendingMachineResponse,
    ApiResponse,
)

router = APIRouter(prefix="/vending-machines", tags=["售货机管理"])


@router.post("/", response_model=VendingMachineResponse, summary="创建售货机")
def create_vending_machine(machine: VendingMachineCreate, db: Session = Depends(get_db)):
    """
    创建新售货机
    
    - **name**: 售货机名称（必填）
    - **serial_number**: 设备序列号（必填，唯一）
    - **location**: 安装位置（可选）
    - **region**: 区域标识（可选，用于区域定价）
    - **status**: 设备状态（默认offline）
    - **row_count**: 货道行数（默认6）
    - **column_count**: 货道列数（默认8）
    - **description**: 设备描述（可选）
    """
    # 检查序列号是否已存在
    existing = db.query(VendingMachine).filter(VendingMachine.serial_number == machine.serial_number).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"设备序列号 '{machine.serial_number}' 已存在")
    
    db_machine = VendingMachine(**machine.model_dump())
    try:
        db.add(db_machine)
        db.commit()
        db.refresh(db_machine)
        return db_machine
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="创建售货机失败")


@router.get("/", response_model=List[VendingMachineResponse], summary="获取售货机列表")
def get_vending_machines(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(50, ge=1, le=1000, description="返回数量限制"),
    status: Optional[str] = Query(None, description="状态筛选"),
    region: Optional[str] = Query(None, description="区域筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索（名称、序列号、位置）"),
    db: Session = Depends(get_db),
):
    """
    获取售货机列表，支持分页、状态筛选、区域筛选和关键词搜索
    """
    query = db.query(VendingMachine)
    
    # 状态筛选
    if status:
        query = query.filter(VendingMachine.status == status)
    
    # 区域筛选
    if region:
        query = query.filter(VendingMachine.region == region)
    
    # 关键词搜索
    if keyword:
        query = query.filter(
            (VendingMachine.name.contains(keyword)) |
            (VendingMachine.serial_number.contains(keyword)) |
            (VendingMachine.location.contains(keyword))
        )
    
    # 排序：按创建时间倒序
    query = query.order_by(VendingMachine.created_at.desc())
    
    machines = query.offset(skip).limit(limit).all()
    return machines


@router.get("/{machine_id}", response_model=VendingMachineResponse, summary="获取单个售货机")
def get_vending_machine(machine_id: int, db: Session = Depends(get_db)):
    """
    根据ID获取单个售货机详情
    """
    machine = db.query(VendingMachine).filter(VendingMachine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail=f"售货机 ID {machine_id} 不存在")
    return machine


@router.put("/{machine_id}", response_model=VendingMachineResponse, summary="更新售货机")
def update_vending_machine(
    machine_id: int,
    machine: VendingMachineUpdate,
    db: Session = Depends(get_db),
):
    """
    更新售货机信息
    """
    db_machine = db.query(VendingMachine).filter(VendingMachine.id == machine_id).first()
    if not db_machine:
        raise HTTPException(status_code=404, detail=f"售货机 ID {machine_id} 不存在")
    
    update_data = machine.model_dump(exclude_unset=True)
    
    # 检查序列号是否与其他售货机重复
    if "serial_number" in update_data and update_data["serial_number"] != db_machine.serial_number:
        existing = db.query(VendingMachine).filter(
            VendingMachine.serial_number == update_data["serial_number"],
            VendingMachine.id != machine_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"设备序列号 '{update_data['serial_number']}' 已存在")
    
    # 更新字段
    for key, value in update_data.items():
        setattr(db_machine, key, value)
    
    try:
        db.commit()
        db.refresh(db_machine)
        return db_machine
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="更新售货机失败")


@router.delete("/{machine_id}", response_model=ApiResponse, summary="删除售货机")
def delete_vending_machine(machine_id: int, db: Session = Depends(get_db)):
    """
    删除售货机（注意：如果售货机下有货道，删除将失败）
    """
    db_machine = db.query(VendingMachine).filter(VendingMachine.id == machine_id).first()
    if not db_machine:
        raise HTTPException(status_code=404, detail=f"售货机 ID {machine_id} 不存在")
    
    # 检查售货机下是否有货道
    aisle_count = db.query(Aisle).filter(Aisle.vending_machine_id == machine_id).count()
    if aisle_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"售货机 '{db_machine.name}' 下存在 {aisle_count} 个货道，无法删除"
        )
    
    try:
        db.delete(db_machine)
        db.commit()
        return ApiResponse(success=True, message=f"售货机 '{db_machine.name}' 删除成功")
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="删除售货机失败")
