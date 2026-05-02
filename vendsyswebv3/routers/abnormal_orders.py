"""
异常订单处理API路由
包含异常订单的创建、查询、退款、补发等功能
"""
import math
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from database import get_async_session
from models import Order, AbnormalOrder, VendingMachine, User
from models import (
    AbnormalType, AbnormalStatus, OrderStatus, PaymentStatus, DeliveryStatus
)
from schemas import (
    AbnormalOrderCreate, AbnormalOrderQuery, AbnormalOrderRefund,
    AbnormalOrderRedispatch, AbnormalOrderResponse, PaginatedResponse,
    BaseResponse, AbnormalStatistics
)

# 创建路由
router = APIRouter(prefix="/api/abnormal-orders", tags=["异常订单处理"])


@router.get("/statistics", response_model=BaseResponse)
async def get_abnormal_statistics(
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    session: AsyncSession = Depends(get_async_session)
) -> BaseResponse:
    """
    获取异常订单统计信息
    """
    try:
        # 构建查询条件
        conditions = []
        if start_time:
            conditions.append(AbnormalOrder.created_at >= start_time)
        if end_time:
            conditions.append(AbnormalOrder.created_at <= end_time)
        
        base_query = select(AbnormalOrder)
        if conditions:
            base_query = base_query.where(and_(*conditions))
        
        # 总异常订单数
        count_query = select(func.count(AbnormalOrder.id)).select_from(AbnormalOrder)
        if conditions:
            count_query = count_query.where(and_(*conditions))
        
        count_result = await session.execute(count_query)
        total_abnormal = count_result.scalar() or 0
        
        # 按状态统计
        stats = {
            "total_abnormal": total_abnormal,
            "pending": 0,
            "resolved": 0,
            "paid_no_delivery": 0,
            "delivery_failed": 0,
            "duplicate_payment": 0,
            "other": 0
        }
        
        # 按处理状态统计
        for status_enum in [AbnormalStatus.PENDING, AbnormalStatus.PROCESSING]:
            status_query = select(func.count(AbnormalOrder.id)).where(
                AbnormalOrder.status == status_enum
            )
            if conditions:
                status_query = status_query.where(and_(*conditions))
            
            result = await session.execute(status_query)
            count = result.scalar() or 0
            stats["pending"] += count
        
        # 已解决状态
        for status_enum in [
            AbnormalStatus.REFUNDED, AbnormalStatus.REDISPATCHED,
            AbnormalStatus.RESOLVED, AbnormalStatus.CLOSED
        ]:
            status_query = select(func.count(AbnormalOrder.id)).where(
                AbnormalOrder.status == status_enum
            )
            if conditions:
                status_query = status_query.where(and_(*conditions))
            
            result = await session.execute(status_query)
            count = result.scalar() or 0
            stats["resolved"] += count
        
        # 按异常类型统计
        type_mapping = {
            AbnormalType.PAID_NO_DELIVERY: "paid_no_delivery",
            AbnormalType.DELIVERY_FAILED: "delivery_failed",
            AbnormalType.DUPLICATE_PAYMENT: "duplicate_payment",
        }
        
        for type_enum, field in type_mapping.items():
            type_query = select(func.count(AbnormalOrder.id)).where(
                AbnormalOrder.abnormal_type == type_enum
            )
            if conditions:
                type_query = type_query.where(and_(*conditions))
            
            result = await session.execute(type_query)
            count = result.scalar() or 0
            stats[field] = count
        
        # 其他异常类型统计
        other_types = [AbnormalType.OVER_PAYMENT, AbnormalType.SYSTEM_ERROR, AbnormalType.OTHER]
        for type_enum in other_types:
            type_query = select(func.count(AbnormalOrder.id)).where(
                AbnormalOrder.abnormal_type == type_enum
            )
            if conditions:
                type_query = type_query.where(and_(*conditions))
            
            result = await session.execute(type_query)
            count = result.scalar() or 0
            stats["other"] += count
        
        return BaseResponse(
            code=200,
            message="获取异常订单统计成功",
            data=stats
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计信息失败: {str(e)}"
        )


@router.get("", response_model=PaginatedResponse)
async def get_abnormal_order_list(
    query_params: AbnormalOrderQuery = Depends(),
    session: AsyncSession = Depends(get_async_session)
) -> PaginatedResponse:
    """
    获取异常订单列表（分页）
    
    支持按订单ID、异常类型、处理状态筛选
    """
    try:
        page = query_params.page
        page_size = query_params.page_size
        
        # 构建查询条件
        conditions = []
        
        if query_params.order_id:
            conditions.append(AbnormalOrder.order_id == query_params.order_id)
        
        if query_params.abnormal_type:
            conditions.append(AbnormalOrder.abnormal_type == query_params.abnormal_type)
        
        if query_params.status:
            conditions.append(AbnormalOrder.status == query_params.status)
        
        # 查询总记录数
        count_query = select(func.count(AbnormalOrder.id)).select_from(AbnormalOrder)
        if conditions:
            count_query = count_query.where(and_(*conditions))
        
        count_result = await session.execute(count_query)
        total = count_result.scalar() or 0
        
        # 计算分页信息
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        offset = (page - 1) * page_size
        
        # 查询数据（带关联）
        query = select(AbnormalOrder).options(
            selectinload(AbnormalOrder.order).options(
                selectinload(Order.user),
                selectinload(Order.machine),
                selectinload(Order.order_items)
            )
        )
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # 按创建时间倒序排列
        query = query.order_by(AbnormalOrder.created_at.desc()).offset(offset).limit(page_size)
        
        result = await session.execute(query)
        abnormal_orders = result.scalars().all()
        
        # 转换为响应数据
        items = []
        for ab_order in abnormal_orders:
            ab_dict = {
                "id": ab_order.id,
                "order_id": ab_order.order_id,
                "abnormal_type": ab_order.abnormal_type.value if ab_order.abnormal_type else None,
                "abnormal_description": ab_order.abnormal_description,
                "abnormal_time": ab_order.abnormal_time.isoformat() if ab_order.abnormal_time else None,
                "status": ab_order.status.value if ab_order.status else None,
                "refund_amount": float(ab_order.refund_amount) if ab_order.refund_amount else None,
                "refund_reason": ab_order.refund_reason,
                "refund_approved_at": ab_order.refund_approved_at.isoformat() if ab_order.refund_approved_at else None,
                "refund_completed_at": ab_order.refund_completed_at.isoformat() if ab_order.refund_completed_at else None,
                "redispatch_approved_at": ab_order.redispatch_approved_at.isoformat() if ab_order.redispatch_approved_at else None,
                "redispatch_completed_at": ab_order.redispatch_completed_at.isoformat() if ab_order.redispatch_completed_at else None,
                "handled_by": ab_order.handled_by,
                "created_at": ab_order.created_at.isoformat() if ab_order.created_at else None,
                "updated_at": ab_order.updated_at.isoformat() if ab_order.updated_at else None
            }
            
            # 订单信息
            if ab_order.order:
                order = ab_order.order
                ab_dict["order"] = {
                    "id": order.id,
                    "order_no": order.order_no,
                    "total_amount": float(order.total_amount),
                    "pay_amount": float(order.pay_amount),
                    "order_status": order.order_status.value if order.order_status else None,
                    "payment_status": order.payment_status.value if order.payment_status else None,
                    "delivery_status": order.delivery_status.value if order.delivery_status else None,
                    "created_at": order.created_at.isoformat() if order.created_at else None
                }
                
                # 用户信息
                if order.user:
                    ab_dict["order"]["user"] = {
                        "id": order.user.id,
                        "phone": order.user.phone,
                        "nickname": order.user.nickname
                    }
                
                # 售货机信息
                if order.machine:
                    ab_dict["order"]["machine"] = {
                        "id": order.machine.id,
                        "machine_code": order.machine.machine_code,
                        "machine_name": order.machine.machine_name,
                        "location": order.machine.location
                    }
                
                # 商品明细数量
                ab_dict["order"]["item_count"] = len(order.order_items) if order.order_items else 0
            
            items.append(ab_dict)
        
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
            detail=f"获取异常订单列表失败: {str(e)}"
        )


@router.get("/{abnormal_order_id}", response_model=BaseResponse)
async def get_abnormal_order_detail(
    abnormal_order_id: str,
    session: AsyncSession = Depends(get_async_session)
) -> BaseResponse:
    """
    获取异常订单详情
    
    包含异常订单信息、关联订单信息
    """
    try:
        query = select(AbnormalOrder).options(
            selectinload(AbnormalOrder.order).options(
                selectinload(Order.user),
                selectinload(Order.machine),
                selectinload(Order.order_items)
            )
        ).where(AbnormalOrder.id == abnormal_order_id)
        
        result = await session.execute(query)
        ab_order = result.scalar_one_or_none()
        
        if not ab_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="异常订单不存在"
            )
        
        # 构建响应数据
        ab_data = {
            "id": ab_order.id,
            "order_id": ab_order.order_id,
            "abnormal_type": ab_order.abnormal_type.value if ab_order.abnormal_type else None,
            "abnormal_description": ab_order.abnormal_description,
            "abnormal_time": ab_order.abnormal_time.isoformat() if ab_order.abnormal_time else None,
            "status": ab_order.status.value if ab_order.status else None,
            "refund_amount": float(ab_order.refund_amount) if ab_order.refund_amount else None,
            "refund_reason": ab_order.refund_reason,
            "refund_remark": ab_order.refund_remark,
            "refund_approved_at": ab_order.refund_approved_at.isoformat() if ab_order.refund_approved_at else None,
            "refund_completed_at": ab_order.refund_completed_at.isoformat() if ab_order.refund_completed_at else None,
            "redispatch_machine_id": ab_order.redispatch_machine_id,
            "redispatch_remark": ab_order.redispatch_remark,
            "redispatch_approved_at": ab_order.redispatch_approved_at.isoformat() if ab_order.redispatch_approved_at else None,
            "redispatch_completed_at": ab_order.redispatch_completed_at.isoformat() if ab_order.redispatch_completed_at else None,
            "handled_by": ab_order.handled_by,
            "handler_remark": ab_order.handler_remark,
            "created_at": ab_order.created_at.isoformat() if ab_order.created_at else None,
            "updated_at": ab_order.updated_at.isoformat() if ab_order.updated_at else None
        }
        
        # 订单信息
        if ab_order.order:
            order = ab_order.order
            ab_data["order"] = {
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
                "created_at": order.created_at.isoformat() if order.created_at else None,
                "paid_at": order.paid_at.isoformat() if order.paid_at else None,
                "delivered_at": order.delivered_at.isoformat() if order.delivered_at else None
            }
            
            # 用户信息
            if order.user:
                ab_data["order"]["user"] = {
                    "id": order.user.id,
                    "user_code": order.user.user_code,
                    "phone": order.user.phone,
                    "nickname": order.user.nickname,
                    "avatar_url": order.user.avatar_url
                }
            
            # 售货机信息
            if order.machine:
                ab_data["order"]["machine"] = {
                    "id": order.machine.id,
                    "machine_code": order.machine.machine_code,
                    "machine_name": order.machine.machine_name,
                    "location": order.machine.location,
                    "address": order.machine.address
                }
            
            # 商品明细
            if order.order_items:
                ab_data["order"]["items"] = []
                for item in order.order_items:
                    ab_data["order"]["items"].append({
                        "id": item.id,
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
            message="获取异常订单详情成功",
            data=ab_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取异常订单详情失败: {str(e)}"
        )


@router.post("", response_model=BaseResponse)
async def create_abnormal_order(
    ab_data: AbnormalOrderCreate,
    session: AsyncSession = Depends(get_async_session)
) -> BaseResponse:
    """
    创建异常订单记录
    
    通常由系统自动检测或用户投诉触发
    """
    try:
        # 验证订单存在
        order_query = select(Order).where(Order.id == ab_data.order_id)
        order_result = await session.execute(order_query)
        order = order_result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="订单不存在"
            )
        
        # 检查是否已存在异常订单
        exist_query = select(AbnormalOrder).where(AbnormalOrder.order_id == ab_data.order_id)
        exist_result = await session.execute(exist_query)
        exist_ab = exist_result.scalar_one_or_none()
        
        if exist_ab:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该订单已存在异常记录"
            )
        
        # 更新原订单状态为异常
        order.order_status = OrderStatus.ABNORMAL
        
        # 创建异常订单
        abnormal_order = AbnormalOrder(
            order_id=ab_data.order_id,
            abnormal_type=ab_data.abnormal_type,
            abnormal_description=ab_data.abnormal_description,
            abnormal_time=datetime.utcnow(),
            status=AbnormalStatus.PENDING
        )
        
        session.add(abnormal_order)
        await session.commit()
        
        return BaseResponse(
            code=200,
            message="异常订单创建成功",
            data={
                "id": abnormal_order.id,
                "order_id": abnormal_order.order_id,
                "order_no": order.order_no,
                "abnormal_type": abnormal_order.abnormal_type.value,
                "status": abnormal_order.status.value,
                "created_at": abnormal_order.created_at.isoformat() if abnormal_order.created_at else None
            }
        )
        
    except HTTPException:
        await session.rollback()
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建异常订单失败: {str(e)}"
        )


@router.post("/{abnormal_order_id}/refund", response_model=BaseResponse)
async def approve_refund(
    abnormal_order_id: str,
    refund_data: AbnormalOrderRefund,
    session: AsyncSession = Depends(get_async_session)
) -> BaseResponse:
    """
    批准异常订单退款
    
    1. 验证异常订单状态
    2. 检查退款金额是否合理
    3. 更新异常订单和原订单状态
    """
    try:
        # 查询异常订单
        query = select(AbnormalOrder).options(
            selectinload(AbnormalOrder.order)
        ).where(AbnormalOrder.id == abnormal_order_id)
        
        result = await session.execute(query)
        ab_order = result.scalar_one_or_none()
        
        if not ab_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="异常订单不存在"
            )
        
        # 检查状态
        if ab_order.status not in [AbnormalStatus.PENDING, AbnormalStatus.PROCESSING]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该异常订单当前状态不允许退款"
            )
        
        # 验证订单
        if not ab_order.order:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="关联订单不存在"
            )
        
        order = ab_order.order
        
        # 检查退款金额不能超过实付金额
        if refund_data.refund_amount > order.pay_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"退款金额不能超过实付金额 {order.pay_amount} 元"
            )
        
        # 更新异常订单
        ab_order.refund_amount = refund_data.refund_amount
        ab_order.refund_reason = refund_data.refund_reason
        ab_order.refund_remark = refund_data.refund_remark
        ab_order.refund_approved_at = datetime.utcnow()
        ab_order.handled_by = refund_data.handled_by
        ab_order.status = AbnormalStatus.REFUND_APPROVED
        
        # 更新原订单状态
        order.payment_status = PaymentStatus.REFUNDING
        
        await session.commit()
        
        return BaseResponse(
            code=200,
            message="退款已批准，等待实际退款处理",
            data={
                "abnormal_order_id": ab_order.id,
                "order_id": ab_order.order_id,
                "order_no": order.order_no,
                "refund_amount": float(refund_data.refund_amount),
                "refund_reason": refund_data.refund_reason,
                "handled_by": refund_data.handled_by,
                "status": AbnormalStatus.REFUND_APPROVED.value,
                "approved_at": ab_order.refund_approved_at.isoformat() if ab_order.refund_approved_at else None
            }
        )
        
    except HTTPException:
        await session.rollback()
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"审批退款失败: {str(e)}"
        )


@router.post("/{abnormal_order_id}/confirm-refund", response_model=BaseResponse)
async def confirm_refund(
    abnormal_order_id: str,
    handler_remark: Optional[str] = Query(None, description="处理备注"),
    session: AsyncSession = Depends(get_async_session)
) -> BaseResponse:
    """
    确认退款完成
    
    模拟第三方支付平台退款成功回调
    """
    try:
        query = select(AbnormalOrder).options(
            selectinload(AbnormalOrder.order)
        ).where(AbnormalOrder.id == abnormal_order_id)
        
        result = await session.execute(query)
        ab_order = result.scalar_one_or_none()
        
        if not ab_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="异常订单不存在"
            )
        
        if ab_order.status != AbnormalStatus.REFUND_APPROVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该异常订单尚未批准退款"
            )
        
        # 更新异常订单状态
        ab_order.status = AbnormalStatus.REFUNDED
        ab_order.refund_completed_at = datetime.utcnow()
        ab_order.handler_remark = handler_remark
        
        # 更新原订单状态
        if ab_order.order:
            ab_order.order.payment_status = PaymentStatus.REFUNDED
            ab_order.order.order_status = OrderStatus.REFUNDED
        
        await session.commit()
        
        return BaseResponse(
            code=200,
            message="退款已完成",
            data={
                "abnormal_order_id": ab_order.id,
                "order_id": ab_order.order_id,
                "refund_amount": float(ab_order.refund_amount) if ab_order.refund_amount else None,
                "status": AbnormalStatus.REFUNDED.value,
                "completed_at": ab_order.refund_completed_at.isoformat() if ab_order.refund_completed_at else None
            }
        )
        
    except HTTPException:
        await session.rollback()
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"确认退款失败: {str(e)}"
        )


@router.post("/{abnormal_order_id}/redispatch", response_model=BaseResponse)
async def approve_redispatch(
    abnormal_order_id: str,
    redispatch_data: AbnormalOrderRedispatch,
    session: AsyncSession = Depends(get_async_session)
) -> BaseResponse:
    """
    批准异常订单补发
    
    1. 验证异常订单状态
    2. 检查补发售货机
    3. 更新异常订单状态
    """
    try:
        # 查询异常订单
        query = select(AbnormalOrder).options(
            selectinload(AbnormalOrder.order)
        ).where(AbnormalOrder.id == abnormal_order_id)
        
        result = await session.execute(query)
        ab_order = result.scalar_one_or_none()
        
        if not ab_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="异常订单不存在"
            )
        
        # 检查状态
        if ab_order.status not in [AbnormalStatus.PENDING, AbnormalStatus.PROCESSING]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该异常订单当前状态不允许补发"
            )
        
        # 验证补发售货机（如果指定了）
        if redispatch_data.redispatch_machine_id:
            machine_query = select(VendingMachine).where(
                VendingMachine.id == redispatch_data.redispatch_machine_id
            )
            machine_result = await session.execute(machine_query)
            machine = machine_result.scalar_one_or_none()
            
            if not machine:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="指定的补发售货机不存在"
                )
            
            if machine.status != "active":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="指定的补发售货机不可用"
                )
        
        # 更新异常订单
        ab_order.redispatch_machine_id = redispatch_data.redispatch_machine_id
        ab_order.redispatch_remark = redispatch_data.redispatch_remark
        ab_order.redispatch_approved_at = datetime.utcnow()
        ab_order.handled_by = redispatch_data.handled_by
        ab_order.status = AbnormalStatus.REDISPATCH_APPROVED
        
        await session.commit()
        
        return BaseResponse(
            code=200,
            message="补发已批准，等待出货处理",
            data={
                "abnormal_order_id": ab_order.id,
                "order_id": ab_order.order_id,
                "redispatch_machine_id": ab_order.redispatch_machine_id,
                "handled_by": redispatch_data.handled_by,
                "status": AbnormalStatus.REDISPATCH_APPROVED.value,
                "approved_at": ab_order.redispatch_approved_at.isoformat() if ab_order.redispatch_approved_at else None
            }
        )
        
    except HTTPException:
        await session.rollback()
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"审批补发失败: {str(e)}"
        )


@router.post("/{abnormal_order_id}/confirm-redispatch", response_model=BaseResponse)
async def confirm_redispatch(
    abnormal_order_id: str,
    handler_remark: Optional[str] = Query(None, description="处理备注"),
    session: AsyncSession = Depends(get_async_session)
) -> BaseResponse:
    """
    确认补发完成
    
    模拟售货机出货成功回调
    """
    try:
        query = select(AbnormalOrder).options(
            selectinload(AbnormalOrder.order)
        ).where(AbnormalOrder.id == abnormal_order_id)
        
        result = await session.execute(query)
        ab_order = result.scalar_one_or_none()
        
        if not ab_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="异常订单不存在"
            )
        
        if ab_order.status != AbnormalStatus.REDISPATCH_APPROVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该异常订单尚未批准补发"
            )
        
        # 更新异常订单状态
        ab_order.status = AbnormalStatus.REDISPATCHED
        ab_order.redispatch_completed_at = datetime.utcnow()
        ab_order.handler_remark = handler_remark
        
        # 更新原订单状态
        if ab_order.order:
            ab_order.order.delivery_status = DeliveryStatus.SUCCESS
            ab_order.order.delivered_at = datetime.utcnow()
            ab_order.order.order_status = OrderStatus.DELIVERED
        
        await session.commit()
        
        return BaseResponse(
            code=200,
            message="补发已完成",
            data={
                "abnormal_order_id": ab_order.id,
                "order_id": ab_order.order_id,
                "status": AbnormalStatus.REDISPATCHED.value,
                "completed_at": ab_order.redispatch_completed_at.isoformat() if ab_order.redispatch_completed_at else None
            }
        )
        
    except HTTPException:
        await session.rollback()
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"确认补发失败: {str(e)}"
        )


@router.put("/{abnormal_order_id}/close", response_model=BaseResponse)
async def close_abnormal_order(
    abnormal_order_id: str,
    handler_remark: str = Query(..., description="关闭备注"),
    handled_by: str = Query(..., description="处理人"),
    session: AsyncSession = Depends(get_async_session)
) -> BaseResponse:
    """
    关闭/标记异常订单为已解决
    
    适用于无需退款或补发的情况
    """
    try:
        query = select(AbnormalOrder).options(
            selectinload(AbnormalOrder.order)
        ).where(AbnormalOrder.id == abnormal_order_id)
        
        result = await session.execute(query)
        ab_order = result.scalar_one_or_none()
        
        if not ab_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="异常订单不存在"
            )
        
        # 更新异常订单状态
        ab_order.status = AbnormalStatus.CLOSED
        ab_order.handled_by = handled_by
        ab_order.handler_remark = handler_remark
        
        # 恢复原订单状态（如果适用）
        if ab_order.order:
            # 根据支付和出货状态判断最终状态
            order = ab_order.order
            if order.payment_status == PaymentStatus.PAID and order.delivery_status == DeliveryStatus.SUCCESS:
                order.order_status = OrderStatus.DELIVERED
            elif order.payment_status == PaymentStatus.PAID:
                order.order_status = OrderStatus.PAID
            else:
                order.order_status = OrderStatus.CREATED
        
        await session.commit()
        
        return BaseResponse(
            code=200,
            message="异常订单已关闭",
            data={
                "abnormal_order_id": ab_order.id,
                "order_id": ab_order.order_id,
                "status": AbnormalStatus.CLOSED.value,
                "handled_by": handled_by,
                "handler_remark": handler_remark
            }
        )
        
    except HTTPException:
        await session.rollback()
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"关闭异常订单失败: {str(e)}"
        )
