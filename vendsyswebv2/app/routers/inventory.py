from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from app.database import get_db
from app.models import (
    AisleProduct,
    InventoryRecord,
    ReplenishmentOrder,
    VendingMachine,
    Aisle,
    Product,
)
from app.schemas import (
    InventoryRecordResponse,
    ReplenishmentOrderCreate,
    ReplenishmentOrderUpdate,
    ReplenishmentOrderResponse,
    SalesCreate,
    ApiResponse,
)

router = APIRouter(tags=["库存与补货管理"])


@router.post("/sales/", response_model=ApiResponse, summary="销售扣减库存")
def process_sale(sale: SalesCreate, db: Session = Depends(get_db)):
    """
    处理销售，扣减库存
    
    - **aisle_product_id**: 货道商品绑定ID
    - **quantity**: 销售数量
    - **order_number**: 订单号（可选）
    """
    # 检查货道商品绑定是否存在
    binding = db.query(AisleProduct).filter(AisleProduct.id == sale.aisle_product_id).first()
    if not binding:
        raise HTTPException(status_code=404, detail=f"货道商品绑定 ID {sale.aisle_product_id} 不存在")
    
    # 检查库存是否足够
    if binding.current_stock < sale.quantity:
        raise HTTPException(
            status_code=400,
            detail=f"库存不足，当前库存: {binding.current_stock}, 需要: {sale.quantity}"
        )
    
    # 记录变更前库存
    before_stock = binding.current_stock
    # 扣减库存
    binding.current_stock -= sale.quantity
    after_stock = binding.current_stock
    
    # 创建库存记录
    inventory_record = InventoryRecord(
        aisle_product_id=sale.aisle_product_id,
        change_type="sale",
        change_quantity=-sale.quantity,
        before_stock=before_stock,
        after_stock=after_stock,
        order_number=sale.order_number,
        remark=f"销售扣减库存，数量: {sale.quantity}",
    )
    
    # 检查是否需要生成补货单
    need_replenishment = False
    if binding.current_stock <= binding.stock_threshold:
        # 检查是否已有未完成的补货单
        existing_order = db.query(ReplenishmentOrder).filter(
            ReplenishmentOrder.aisle_product_id == sale.aisle_product_id,
            ReplenishmentOrder.status.in_(["pending", "in_progress"])
        ).first()
        
        if not existing_order:
            # 生成补货单
            replenishment_order = ReplenishmentOrder(
                order_number=f"RO{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                vending_machine_id=binding.aisle.vending_machine_id,
                aisle_product_id=sale.aisle_product_id,
                current_stock=binding.current_stock,
                stock_threshold=binding.stock_threshold,
                suggested_quantity=binding.aisle.max_capacity - binding.current_stock,
                priority="medium",
            )
            # 根据库存情况调整优先级
            if binding.current_stock == 0:
                replenishment_order.priority = "urgent"
            elif binding.current_stock <= binding.stock_threshold * 0.5:
                replenishment_order.priority = "high"
            
            db.add(replenishment_order)
            need_replenishment = True
    
    db.add(inventory_record)
    
    try:
        db.commit()
        message = f"销售处理成功，扣减库存 {sale.quantity} 件"
        if need_replenishment:
            message += "，已自动生成补货单"
        return ApiResponse(success=True, message=message)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="处理销售失败")


@router.post("/inventory/restock/", response_model=ApiResponse, summary="补货操作")
def restock_inventory(
    binding_id: int,
    quantity: int = Query(..., gt=0, description="补货数量"),
    operator_id: Optional[int] = Query(None, description="操作人ID"),
    db: Session = Depends(get_db),
):
    """
    补货操作，增加库存
    
    - **binding_id**: 货道商品绑定ID
    - **quantity**: 补货数量
    - **operator_id**: 操作人ID（可选）
    """
    # 检查货道商品绑定是否存在
    binding = db.query(AisleProduct).filter(AisleProduct.id == binding_id).first()
    if not binding:
        raise HTTPException(status_code=404, detail=f"货道商品绑定 ID {binding_id} 不存在")
    
    # 检查是否超过最大容量
    max_possible = binding.aisle.max_capacity - binding.current_stock
    if quantity > max_possible:
        raise HTTPException(
            status_code=400,
            detail=f"补货数量超过最大容量，最多可补: {max_possible}"
        )
    
    # 记录变更前库存
    before_stock = binding.current_stock
    # 增加库存
    binding.current_stock += quantity
    after_stock = binding.current_stock
    
    # 创建库存记录
    inventory_record = InventoryRecord(
        aisle_product_id=binding_id,
        change_type="restock",
        change_quantity=quantity,
        before_stock=before_stock,
        after_stock=after_stock,
        operator_id=operator_id,
        remark=f"补货操作，数量: {quantity}",
    )
    
    db.add(inventory_record)
    
    try:
        db.commit()
        return ApiResponse(success=True, message=f"补货成功，增加库存 {quantity} 件，当前库存: {after_stock}")
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="补货操作失败")


@router.get("/inventory/records/", response_model=List[InventoryRecordResponse], summary="获取库存记录列表")
def get_inventory_records(
    binding_id: Optional[int] = Query(None, description="货道商品绑定ID筛选"),
    change_type: Optional[str] = Query(None, description="变更类型筛选"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(50, ge=1, le=1000, description="返回数量限制"),
    db: Session = Depends(get_db),
):
    """
    获取库存变更记录
    """
    query = db.query(InventoryRecord)
    
    if binding_id:
        query = query.filter(InventoryRecord.aisle_product_id == binding_id)
    
    if change_type:
        query = query.filter(InventoryRecord.change_type == change_type)
    
    # 按时间倒序
    query = query.order_by(InventoryRecord.created_at.desc())
    
    records = query.offset(skip).limit(limit).all()
    return records


@router.get("/inventory/low-stock/", response_model=List[dict], summary="获取低库存列表")
def get_low_stock_items(
    machine_id: Optional[int] = Query(None, description="售货机ID筛选"),
    db: Session = Depends(get_db),
):
    """
    获取所有库存低于阈值的货道商品
    """
    query = db.query(AisleProduct).options(
        joinedload(AisleProduct.product),
        joinedload(AisleProduct.aisle).joinedload(Aisle.vending_machine)
    ).filter(
        AisleProduct.current_stock <= AisleProduct.stock_threshold,
        AisleProduct.status == "active"
    )
    
    if machine_id:
        query = query.join(Aisle).filter(Aisle.vending_machine_id == machine_id)
    
    low_stock_items = query.all()
    
    result = []
    for item in low_stock_items:
        result.append({
            "id": item.id,
            "aisle_code": item.aisle.aisle_code if item.aisle else None,
            "machine_name": item.aisle.vending_machine.name if item.aisle and item.aisle.vending_machine else None,
            "product_name": item.product.name if item.product else None,
            "current_stock": item.current_stock,
            "stock_threshold": item.stock_threshold,
            "is_empty": item.current_stock == 0,
        })
    
    return result


@router.get("/replenishment-orders/", response_model=List[ReplenishmentOrderResponse], summary="获取补货单列表")
def get_replenishment_orders(
    status: Optional[str] = Query(None, description="状态筛选"),
    priority: Optional[str] = Query(None, description="优先级筛选"),
    machine_id: Optional[int] = Query(None, description="售货机ID筛选"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(50, ge=1, le=1000, description="返回数量限制"),
    db: Session = Depends(get_db),
):
    """
    获取补货单列表
    """
    query = db.query(ReplenishmentOrder)
    
    if status:
        query = query.filter(ReplenishmentOrder.status == status)
    
    if priority:
        query = query.filter(ReplenishmentOrder.priority == priority)
    
    if machine_id:
        query = query.filter(ReplenishmentOrder.vending_machine_id == machine_id)
    
    # 按优先级和创建时间排序
    query = query.order_by(
        ReplenishmentOrder.priority.desc(),
        ReplenishmentOrder.created_at.desc()
    )
    
    orders = query.offset(skip).limit(limit).all()
    return orders


@router.get("/replenishment-orders/{order_id}", response_model=ReplenishmentOrderResponse, summary="获取单个补货单")
def get_replenishment_order(order_id: int, db: Session = Depends(get_db)):
    """
    根据ID获取单个补货单详情
    """
    order = db.query(ReplenishmentOrder).filter(ReplenishmentOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"补货单 ID {order_id} 不存在")
    return order


@router.post("/replenishment-orders/", response_model=ReplenishmentOrderResponse, summary="创建补货单")
def create_replenishment_order(order: ReplenishmentOrderCreate, db: Session = Depends(get_db)):
    """
    手动创建补货单
    """
    # 检查货道商品绑定是否存在
    binding = db.query(AisleProduct).filter(AisleProduct.id == order.aisle_product_id).first()
    if not binding:
        raise HTTPException(status_code=404, detail=f"货道商品绑定 ID {order.aisle_product_id} 不存在")
    
    # 生成订单号（如果未提供）
    if not order.order_number:
        order.order_number = f"RO{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    db_order = ReplenishmentOrder(**order.model_dump())
    
    try:
        db.add(db_order)
        db.commit()
        db.refresh(db_order)
        return db_order
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="创建补货单失败")


@router.put("/replenishment-orders/{order_id}", response_model=ReplenishmentOrderResponse, summary="更新补货单")
def update_replenishment_order(
    order_id: int,
    order: ReplenishmentOrderUpdate,
    db: Session = Depends(get_db),
):
    """
    更新补货单信息
    """
    db_order = db.query(ReplenishmentOrder).filter(ReplenishmentOrder.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail=f"补货单 ID {order_id} 不存在")
    
    update_data = order.model_dump(exclude_unset=True)
    
    # 如果状态变为completed，且有实际补货数量，则执行补货
    if "status" in update_data and update_data["status"] == "completed":
        if db_order.status != "completed":
            # 查找对应的货道商品绑定
            binding = db.query(AisleProduct).filter(
                AisleProduct.id == db_order.aisle_product_id
            ).first()
            
            if binding:
                # 获取实际补货数量
                actual_qty = update_data.get("actual_quantity") if "actual_quantity" in update_data else db_order.actual_quantity
                if actual_qty and actual_qty > 0:
                    # 执行补货
                    before_stock = binding.current_stock
                    binding.current_stock += actual_qty
                    after_stock = binding.current_stock
                    
                    # 创建库存记录
                    inventory_record = InventoryRecord(
                        aisle_product_id=db_order.aisle_product_id,
                        change_type="restock",
                        change_quantity=actual_qty,
                        before_stock=before_stock,
                        after_stock=after_stock,
                        remark=f"补货单 {db_order.order_number} 补货，数量: {actual_qty}",
                    )
                    db.add(inventory_record)
            
            # 设置完成时间
            db_order.completed_at = datetime.utcnow()
    
    # 更新字段
    for key, value in update_data.items():
        setattr(db_order, key, value)
    
    try:
        db.commit()
        db.refresh(db_order)
        return db_order
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="更新补货单失败")


@router.get("/replenishment-orders/stats/overview/", response_model=dict, summary="获取补货统计概览")
def get_replenishment_stats(db: Session = Depends(get_db)):
    """
    获取补货统计概览
    """
    # 统计各状态补货单数量
    pending_count = db.query(ReplenishmentOrder).filter(ReplenishmentOrder.status == "pending").count()
    in_progress_count = db.query(ReplenishmentOrder).filter(ReplenishmentOrder.status == "in_progress").count()
    completed_count = db.query(ReplenishmentOrder).filter(ReplenishmentOrder.status == "completed").count()
    
    # 统计紧急和高优先级补货单
    urgent_count = db.query(ReplenishmentOrder).filter(
        ReplenishmentOrder.status.in_(["pending", "in_progress"]),
        ReplenishmentOrder.priority == "urgent"
    ).count()
    
    high_count = db.query(ReplenishmentOrder).filter(
        ReplenishmentOrder.status.in_(["pending", "in_progress"]),
        ReplenishmentOrder.priority == "high"
    ).count()
    
    # 统计低库存商品数量
    low_stock_count = db.query(AisleProduct).filter(
        AisleProduct.current_stock <= AisleProduct.stock_threshold,
        AisleProduct.status == "active"
    ).count()
    
    return {
        "pending_orders": pending_count,
        "in_progress_orders": in_progress_count,
        "completed_orders": completed_count,
        "urgent_orders": urgent_count,
        "high_priority_orders": high_count,
        "low_stock_items": low_stock_count,
    }
