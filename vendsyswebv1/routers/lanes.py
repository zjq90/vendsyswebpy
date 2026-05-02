"""
货道管理路由
处理设备货道的增删改查操作
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime

from database import get_db
from models import Lane, Device, Product, User
from schemas import LaneCreate, LaneResponse, LaneUpdate
from routers.auth import get_current_user, get_current_admin

router = APIRouter(prefix="/api/lanes", tags=["货道管理"])


@router.get("/device/{device_id}", response_model=List[LaneResponse])
def get_device_lanes(
    device_id: int,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取设备的所有货道
    """
    # 检查设备是否存在
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    query = db.query(Lane).filter(Lane.device_id == device_id)

    if status:
        query = query.filter(Lane.status == status)

    lanes = query.order_by(Lane.lane_number).all()
    return lanes


@router.get("/{lane_id}", response_model=LaneResponse)
def get_lane(
    lane_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取单个货道详情
    """
    lane = db.query(Lane).filter(Lane.id == lane_id).first()
    if not lane:
        raise HTTPException(status_code=404, detail="货道不存在")
    return lane


@router.post("/", response_model=LaneResponse)
def create_lane(
    lane_data: LaneCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    创建货道
    需要管理员权限
    """
    # 检查设备是否存在
    device = db.query(Device).filter(Device.id == lane_data.device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    # 检查货道编号是否已存在于该设备
    existing_lane = db.query(Lane).filter(
        Lane.device_id == lane_data.device_id,
        Lane.lane_number == lane_data.lane_number
    ).first()
    if existing_lane:
        raise HTTPException(status_code=400, detail="该设备中货道编号已存在")

    # 如果指定了商品，检查商品是否存在
    if lane_data.product_id:
        product = db.query(Product).filter(Product.id == lane_data.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="商品不存在")

    new_lane = Lane(**lane_data.dict())
    db.add(new_lane)
    db.commit()
    db.refresh(new_lane)
    return new_lane


@router.post("/batch/init/{device_id}")
def init_device_lanes(
    device_id: int,
    lane_count: int = Query(10, ge=1, le=60),
    capacity_per_lane: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    批量初始化设备货道
    需要管理员权限
    """
    # 检查设备是否存在
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    # 检查是否已存在货道
    existing_count = db.query(Lane).filter(Lane.device_id == device_id).count()
    if existing_count > 0:
        raise HTTPException(status_code=400, detail=f"该设备已存在{existing_count}个货道，请先删除后再初始化")

    created_count = 0
    for i in range(1, lane_count + 1):
        lane = Lane(
            device_id=device_id,
            lane_number=i,
            lane_code=f"L{i:03d}",
            lane_name=f"货道{i}",
            total_capacity=capacity_per_lane,
            current_stock=0,
            min_stock_threshold=2,
            status="empty",
            row=(i - 1) // 10 + 1,  # 每10个一行
            col=(i - 1) % 10 + 1
        )
        db.add(lane)
        created_count += 1

    db.commit()
    return {
        "message": "货道初始化成功",
        "device_id": device_id,
        "created_count": created_count
    }


@router.put("/{lane_id}", response_model=LaneResponse)
def update_lane(
    lane_id: int,
    lane_data: LaneUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    更新货道信息
    需要管理员权限
    """
    lane = db.query(Lane).filter(Lane.id == lane_id).first()
    if not lane:
        raise HTTPException(status_code=404, detail="货道不存在")

    # 如果修改商品，检查商品是否存在
    update_data = lane_data.dict(exclude_unset=True)
    if "product_id" in update_data and update_data["product_id"]:
        product = db.query(Product).filter(Product.id == update_data["product_id"]).first()
        if not product:
            raise HTTPException(status_code=404, detail="商品不存在")

    for key, value in update_data.items():
        setattr(lane, key, value)

    db.commit()
    db.refresh(lane)
    return lane


@router.put("/refill/{lane_id}")
def refill_lane(
    lane_id: int,
    quantity: int = Query(..., gt=0, description="补货数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    货道补货
    需要管理员权限
    """
    lane = db.query(Lane).filter(Lane.id == lane_id).first()
    if not lane:
        raise HTTPException(status_code=404, detail="货道不存在")

    # 检查是否有商品
    if not lane.product_id:
        raise HTTPException(status_code=400, detail="货道未分配商品，请先分配商品")

    # 计算新库存
    new_stock = lane.current_stock + quantity
    if new_stock > lane.total_capacity:
        raise HTTPException(
            status_code=400,
            detail=f"库存超出容量，当前库存{lane.current_stock}，补货{quantity}，容量{lane.total_capacity}"
        )

    lane.current_stock = new_stock
    lane.last_refill_time = datetime.now()
    lane.last_refill_quantity = quantity
    lane.status = "normal"

    db.commit()
    return {
        "message": "补货成功",
        "lane_id": lane_id,
        "previous_stock": lane.current_stock - quantity,
        "current_stock": lane.current_stock,
        "refill_quantity": quantity
    }


@router.delete("/{lane_id}")
def delete_lane(
    lane_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    删除货道
    需要管理员权限
    """
    lane = db.query(Lane).filter(Lane.id == lane_id).first()
    if not lane:
        raise HTTPException(status_code=404, detail="货道不存在")

    db.delete(lane)
    db.commit()
    return {"message": "货道删除成功", "lane_id": lane_id}


@router.get("/stats/device/{device_id}")
def get_device_lane_stats(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取设备货道统计
    """
    from sqlalchemy import func

    # 检查设备是否存在
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    # 统计数据
    total_lanes = db.query(Lane).filter(Lane.device_id == device_id).count()

    # 按状态统计
    status_stats = db.query(
        Lane.status,
        func.count(Lane.id).label('count')
    ).filter(Lane.device_id == device_id).group_by(Lane.status).all()

    # 库存统计
    stock_stats = db.query(
        func.sum(Lane.current_stock).label('total_stock'),
        func.sum(Lane.total_capacity).label('total_capacity'),
        func.count(Lane.id).filter(Lane.current_stock <= Lane.min_stock_threshold).label('low_stock_count')
    ).filter(Lane.device_id == device_id).first()

    # 提取统计值
    total_stock = stock_stats[0] or 0
    total_capacity = stock_stats[1] or 0
    low_stock_count = stock_stats[2] or 0

    # 计算库存百分比（避免除零）
    if total_capacity > 0:
        stock_percentage = round((total_stock / total_capacity) * 100)
    else:
        stock_percentage = 0

    # 构建状态摘要
    status_summary = []
    for s in status_stats:
        status_summary.append({"status": s[0], "count": s[1]})

    stock_summary = {
        "total_stock": total_stock,
        "total_capacity": total_capacity,
        "low_stock_count": low_stock_count,
        "stock_percentage": stock_percentage
    }

    result = {
        "device_id": device_id,
        "device_name": device.device_name,
        "total_lanes": total_lanes,
        "status_summary": status_summary,
        "stock_summary": stock_summary
    }

    return result
