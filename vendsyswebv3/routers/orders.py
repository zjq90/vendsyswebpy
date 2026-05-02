"""
订单管理API路由
包含订单列表、详情、创建、更新等功能
"""
import math
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete, and_, or_
from sqlalchemy.orm import selectinload

from database import get_async_session
from models import Order, OrderItem, Product, User, VendingMachine
from models import (
    OrderStatus, PaymentStatus, DeliveryStatus, PaymentMethod
)
from schemas import (
    OrderCreate, OrderQuery, OrderResponse, OrderStatusUpdate,
    OrderItemResponse, PaginatedResponse, BaseResponse,
    OrderStatistics
)

# 创建路由
router = APIRouter(prefix="/api/orders", tags=["订单管理"])


def generate_order_no() -> str:
    """
    生成订单号
    格式: VM + 时间戳(YYYYMMDDHHMMSS) + 6位随机数
    """
    import random
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_num = str(random.randint(100000, 999999))
    return f"VM{timestamp}{random_num}"


async def get_order_with_details(
    session: AsyncSession,
    order_id: str,
    include_items: bool = True,
    include_user: bool = True,
    include_machine: bool = True
) -> Optional[Order]:
    """
    获取订单及其关联详情
    
    Args:
        session: 数据库会话
        order_id: 订单ID
        include_items: 是否包含商品明细
        include_user: 是否包含用户信息
        include_machine: 是否包含售货机信息
    
    Returns:
        Order对象或None
    """
    query = select(Order).where(Order.id == order_id)
    
    options = []
    if include_items:
        options.append(selectinload(Order.order_items))
    if include_user:
        options.append(selectinload(Order.user))
    if include_machine:
        options.append(selectinload(Order.machine))
    
    if options:
        query = query.options(*options)
    
    result = await session.execute(query)
    return result.scalar_one_or_none()


@router.get("/statistics", response_model=BaseResponse)
async def get_order_statistics(
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    session: AsyncSession = Depends(get_async_session)
) -> BaseResponse:
    """
    获取订单统计信息
    
    统计指定时间范围内的订单数量和金额
    """
    try:
        # 构建基础查询条件
        conditions = []
        if start_time:
            conditions.append(Order.created_at >= start_time)
        if end_time:
            conditions.append(Order.created_at <= end_time)
        
        base_query = select(Order)
        if conditions:
            base_query = base_query.where(and_(*conditions))
        
        # 统计总订单数和总金额
        count_query = select(func.count(Order.id)).select_from(Order)
        amount_query = select(func.sum(Order.pay_amount)).select_from(Order)
        if conditions:
            count_query = count_query.where(and_(*conditions))
            amount_query = amount_query.where(and_(*conditions))
        
        total_count_result = await session.execute(count_query)
        total_count = total_count_result.scalar() or 0
        
        total_amount_result = await session.execute(amount_query)
        total_amount = total_amount_result.scalar() or Decimal(0)
        
        # 按状态统计
        stats = {
            "total_orders": total_count,
            "total_amount": float(total_amount),
            "pending_payment": 0,
            "paid": 0,
            "delivered": 0,
            "cancelled": 0,
            "refunded": 0,
            "abnormal": 0
        }
        
        for status_enum in OrderStatus:
            status_query = select(func.count(Order.id)).where(
                Order.order_status == status_enum
            )
            if conditions:
                status_query = status_query.where(and_(*conditions))
            
            result = await session.execute(status_query)
            count = result.scalar() or 0
            
            # 映射到统计字段
            status_field = status_enum.value
            if status_field == "created":
                stats["pending_payment"] += count
            elif status_field in stats:
                stats[status_field] = count
        
        return BaseResponse(
            code=200,
            message="获取统计信息成功",
            data=stats
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计信息失败: {str(e)}"
        )


@router.get("", response_model=PaginatedResponse)
async def get_order_list(
    query_params: OrderQuery = Depends(),
    session: AsyncSession = Depends(get_async_session)
) -> PaginatedResponse:
    """
    获取订单列表（分页）
    
    支持按订单号、用户、售货机、状态、支付方式、时间范围筛选
    """
    try:
        page = query_params.page
        page_size = query_params.page_size
        
        # 构建查询条件
        conditions = []
        
        if query_params.order_no:
            conditions.append(Order.order_no.ilike(f"%{query_params.order_no}%"))
        
        if query_params.user_id:
            conditions.append(Order.user_id == query_params.user_id)
        
        if query_params.machine_id:
            conditions.append(Order.machine_id == query_params.machine_id)
        
        if query_params.order_status:
            conditions.append(Order.order_status == query_params.order_status)
        
        if query_params.payment_status:
            conditions.append(Order.payment_status == query_params.payment_status)
        
        if query_params.payment_method:
            conditions.append(Order.payment_method == query_params.payment_method)
        
        if query_params.start_time:
            conditions.append(Order.created_at >= query_params.start_time)
        
        if query_params.end_time:
            conditions.append(Order.created_at <= query_params.end_time)
        
        # 查询总记录数
        count_query = select(func.count(Order.id)).select_from(Order)
        if conditions:
            count_query = count_query.where(and_(*conditions))
        
        count_result = await session.execute(count_query)
        total = count_result.scalar() or 0
        
        # 计算分页信息
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        offset = (page - 1) * page_size
        
        # 查询数据（带关联）
        query = select(Order).options(
            selectinload(Order.user),
            selectinload(Order.machine),
            selectinload(Order.order_items)
        )
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # 按创建时间倒序排列
        query = query.order_by(Order.created_at.desc()).offset(offset).limit(page_size)
        
        result = await session.execute(query)
        orders = result.scalars().all()
        
        # 转换为响应数据
        items = []
        for order in orders:
            order_dict = {
                "id": order.id,
                "order_no": order.order_no,
                "user_id": order.user_id,
                "machine_id": order.machine_id,
                "total_amount": float(order.total_amount),
                "discount_amount": float(order.discount_amount),
                "pay_amount": float(order.pay_amount),
                "payment_method": order.payment_method.value if order.payment_method else None,
                "payment_status": order.payment_status.value if order.payment_status else None,
                "delivery_status": order.delivery_status.value if order.delivery_status else None,
                "order_status": order.order_status.value if order.order_status else None,
                "created_at": order.created_at.isoformat() if order.created_at else None,
                "paid_at": order.paid_at.isoformat() if order.paid_at else None,
                "delivered_at": order.delivered_at.isoformat() if order.delivered_at else None
            }
            
            # 用户信息
            if order.user:
                order_dict["user"] = {
                    "id": order.user.id,
                    "user_code": order.user.user_code,
                    "phone": order.user.phone,
                    "nickname": order.user.nickname
                }
            
            # 售货机信息
            if order.machine:
                order_dict["machine"] = {
                    "id": order.machine.id,
                    "machine_code": order.machine.machine_code,
                    "machine_name": order.machine.machine_name,
                    "location": order.machine.location
                }
            
            # 商品数量
            order_dict["item_count"] = len(order.order_items) if order.order_items else 0
            
            items.append(order_dict)
        
        return PaginatedResponse(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            items=items
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取订单列表失败: {str(e)}"
        )


@router.get("/{order_id}", response_model=BaseResponse)
async def get_order_detail(
    order_id: str,
    session: AsyncSession = Depends(get_async_session)
) -> BaseResponse:
    """
    获取订单详情
    
    包含订单基本信息、用户信息、售货机信息、商品明细
    """
    try:
        order = await get_order_with_details(session, order_id)
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="订单不存在"
            )
        
        # 构建响应数据
        order_data = {
            "id": order.id,
            "order_no": order.order_no,
            "user_id": order.user_id,
            "machine_id": order.machine_id,
            "total_amount": float(order.total_amount),
            "discount_amount": float(order.discount_amount),
            "pay_amount": float(order.pay_amount),
            "payment_method": order.payment_method.value if order.payment_method else None,
            "payment_status": order.payment_status.value if order.payment_status else None,
            "third_party_order_no": order.third_party_order_no,
            "delivery_status": order.delivery_status.value if order.delivery_status else None,
            "order_status": order.order_status.value if order.order_status else None,
            "remark": order.remark,
            "cancel_reason": order.cancel_reason,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "paid_at": order.paid_at.isoformat() if order.paid_at else None,
            "delivered_at": order.delivered_at.isoformat() if order.delivered_at else None,
            "updated_at": order.updated_at.isoformat() if order.updated_at else None
        }
        
        # 用户信息
        if order.user:
            order_data["user"] = {
                "id": order.user.id,
                "user_code": order.user.user_code,
                "phone": order.user.phone,
                "nickname": order.user.nickname,
                "avatar_url": order.user.avatar_url
            }
        
        # 售货机信息
        if order.machine:
            order_data["machine"] = {
                "id": order.machine.id,
                "machine_code": order.machine.machine_code,
                "machine_name": order.machine.machine_name,
                "location": order.machine.location,
                "address": order.machine.address
            }
        
        # 商品明细
        if order.order_items:
            order_data["items"] = []
            for item in order.order_items:
                order_data["items"].append({
                    "id": item.id,
                    "product_id": item.product_id,
                    "product_code": item.product_code,
                    "product_name": item.product_name,
                    "quantity": item.quantity,
                    "unit_price": float(item.unit_price),
                    "subtotal_amount": float(item.subtotal_amount),
                    "delivery_status": item.delivery_status.value if item.delivery_status else None,
                    "delivered_quantity": item.delivered_quantity
                })
        
        return BaseResponse(
            code=200,
            message="获取订单详情成功",
            data=order_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取订单详情失败: {str(e)}"
        )


@router.post("", response_model=BaseResponse)
async def create_order(
    order_data: OrderCreate,
    session: AsyncSession = Depends(get_async_session)
) -> BaseResponse:
    """
    创建订单
    
    1. 验证商品存在和库存
    2. 计算订单金额
    3. 创建订单和订单明细
    """
    try:
        # 验证售货机存在
        machine_query = select(VendingMachine).where(VendingMachine.id == order_data.machine_id)
        machine_result = await session.execute(machine_query)
        machine = machine_result.scalar_one_or_none()
        
        if not machine:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="售货机不存在"
            )
        
        if machine.status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="售货机当前不可用"
            )
        
        # 验证用户存在（如果提供了user_id）
        user = None
        if order_data.user_id:
            user_query = select(User).where(User.id == order_data.user_id)
            user_result = await session.execute(user_query)
            user = user_result.scalar_one_or_none()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="用户不存在"
                )
        
        # 验证商品并计算金额
        total_amount = Decimal(0)
        order_items = []
        
        for item_data in order_data.items:
            # 查询商品
            product_query = select(Product).where(Product.id == item_data.product_id)
            product_result = await session.execute(product_query)
            product = product_result.scalar_one_or_none()
            
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"商品ID {item_data.product_id} 不存在"
                )
            
            if product.status != "active":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"商品 {product.product_name} 已下架"
                )
            
            # 计算小计
            subtotal = product.price * item_data.quantity
            total_amount += subtotal
            
            # 创建订单明细
            order_item = OrderItem(
                product_id=product.id,
                product_code=product.product_code,
                product_name=product.product_name,
                quantity=item_data.quantity,
                unit_price=product.price,
                subtotal_amount=subtotal,
                delivery_status=DeliveryStatus.PENDING,
                delivered_quantity=0
            )
            order_items.append(order_item)
        
        # 创建订单
        order_no = generate_order_no()
        
        order = Order(
            order_no=order_no,
            user_id=order_data.user_id,
            machine_id=order_data.machine_id,
            total_amount=total_amount,
            discount_amount=Decimal(0),
            pay_amount=total_amount,
            payment_method=order_data.payment_method,
            payment_status=PaymentStatus.PENDING,
            delivery_status=DeliveryStatus.PENDING,
            order_status=OrderStatus.CREATED,
            remark=order_data.remark
        )
        
        session.add(order)
        await session.flush()  # 刷新以获取订单ID
        
        # 关联订单ID到明细
        for order_item in order_items:
            order_item.order_id = order.id
            session.add(order_item)
        
        await session.commit()
        
        # 返回创建的订单信息
        return BaseResponse(
            code=200,
            message="订单创建成功",
            data={
                "id": order.id,
                "order_no": order.order_no,
                "total_amount": float(order.total_amount),
                "pay_amount": float(order.pay_amount),
                "payment_method": order.payment_method.value,
                "order_status": order.order_status.value,
                "created_at": order.created_at.isoformat() if order.created_at else None
            }
        )
        
    except HTTPException:
        await session.rollback()
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建订单失败: {str(e)}"
        )


@router.put("/{order_id}/status", response_model=BaseResponse)
async def update_order_status(
    order_id: str,
    status_data: OrderStatusUpdate,
    session: AsyncSession = Depends(get_async_session)
) -> BaseResponse:
    """
    更新订单状态
    
    可更新订单状态、支付状态、出货状态
    """
    try:
        # 查询订单
        order = await get_order_with_details(session, order_id, include_items=False)
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="订单不存在"
            )
        
        # 更新字段
        fields_updated = []
        
        if status_data.order_status is not None:
            order.order_status = status_data.order_status
            fields_updated.append("order_status")
            
            # 如果状态变为取消，需要记录取消原因
            if status_data.order_status == OrderStatus.CANCELLED and status_data.remark:
                order.cancel_reason = status_data.remark
        
        if status_data.payment_status is not None:
            order.payment_status = status_data.payment_status
            fields_updated.append("payment_status")
            
            # 如果支付成功，更新支付时间和订单状态
            if status_data.payment_status == PaymentStatus.PAID:
                order.paid_at = datetime.utcnow()
                if order.order_status == OrderStatus.CREATED:
                    order.order_status = OrderStatus.PAID
        
        if status_data.delivery_status is not None:
            order.delivery_status = status_data.delivery_status
            fields_updated.append("delivery_status")
            
            # 如果出货成功，更新出货时间和订单状态
            if status_data.delivery_status == DeliveryStatus.SUCCESS:
                order.delivered_at = datetime.utcnow()
                if order.order_status == OrderStatus.PAID:
                    order.order_status = OrderStatus.DELIVERED
        
        # 更新备注
        if status_data.remark and not order.cancel_reason:
            order.remark = status_data.remark
        
        await session.commit()
        
        return BaseResponse(
            code=200,
            message="订单状态更新成功",
            data={
                "order_id": order.id,
                "order_no": order.order_no,
                "order_status": order.order_status.value,
                "payment_status": order.payment_status.value,
                "delivery_status": order.delivery_status.value,
                "updated_fields": fields_updated
            }
        )
        
    except HTTPException:
        await session.rollback()
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新订单状态失败: {str(e)}"
        )


@router.delete("/{order_id}", response_model=BaseResponse)
async def delete_order(
    order_id: str,
    session: AsyncSession = Depends(get_async_session)
) -> BaseResponse:
    """
    删除订单（逻辑删除，实际只支持取消）
    
    注意：订单通常不应该物理删除，这里只允许取消状态为CREATED的订单
    """
    try:
        order = await get_order_with_details(session, order_id, include_items=False)
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="订单不存在"
            )
        
        # 只有待创建/待支付的订单可以删除
        if order.order_status not in [OrderStatus.CREATED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该订单状态不允许删除"
            )
        
        # 实际执行取消而不是删除
        order.order_status = OrderStatus.CANCELLED
        order.cancel_reason = "用户/管理员删除订单"
        
        await session.commit()
        
        return BaseResponse(
            code=200,
            message="订单已取消（逻辑删除）",
            data={
                "order_id": order.id,
                "order_no": order.order_no,
                "order_status": order.order_status.value
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除订单失败: {str(e)}"
        )
