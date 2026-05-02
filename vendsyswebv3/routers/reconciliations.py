"""
对账管理API路由
包含每日/每月对账、差异处理等功能
"""
import math
from datetime import datetime, timedelta
from typing import Optional, List
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from database import get_async_session
from models import Reconciliation, ReconciliationDetail, Order
from models import (
    ReconciliationStatus, PaymentMethod, PaymentStatus, OrderStatus
)
from schemas import (
    ReconciliationCreate, ReconciliationQuery, ReconciliationResolve,
    PaginatedResponse, BaseResponse
)

# 创建路由
router = APIRouter(prefix="/api/reconciliations", tags=["对账管理"])


def get_recon_date_range(recon_date: str, recon_type: str) -> tuple:
    """
    根据对账日期和类型获取时间范围
    
    Args:
        recon_date: 对账日期，格式为 YYYY-MM-DD 或 YYYY-MM
        recon_type: 对账类型，daily 或 monthly
    
    Returns:
        (start_datetime, end_datetime)
    """
    try:
        if recon_type == "monthly":
            # 月度对账：YYYY-MM
            year, month = map(int, recon_date.split("-"))
            start_dt = datetime(year, month, 1)
            if month == 12:
                end_dt = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_dt = datetime(year, month + 1, 1) - timedelta(days=1)
        else:
            # 每日对账：YYYY-MM-DD
            year, month, day = map(int, recon_date.split("-"))
            start_dt = datetime(year, month, day, 0, 0, 0)
            end_dt = datetime(year, month, day, 23, 59, 59)
        
        return start_dt, end_dt
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"日期格式错误: {str(e)}"
        )


@router.get("", response_model=PaginatedResponse)
async def get_reconciliation_list(
    query_params: ReconciliationQuery = Depends(),
    session: AsyncSession = Depends(get_async_session)
) -> PaginatedResponse:
    """
    获取对账记录列表（分页）
    
    支持按对账日期、类型、支付方式、状态筛选
    """
    try:
        page = query_params.page
        page_size = query_params.page_size
        
        # 构建查询条件
        conditions = []
        
        if query_params.recon_date:
            conditions.append(Reconciliation.recon_date == query_params.recon_date)
        
        if query_params.recon_type:
            conditions.append(Reconciliation.recon_type == query_params.recon_type)
        
        if query_params.payment_method:
            conditions.append(Reconciliation.payment_method == query_params.payment_method)
        
        if query_params.status:
            conditions.append(Reconciliation.status == query_params.status)
        
        # 查询总记录数
        count_query = select(func.count(Reconciliation.id)).select_from(Reconciliation)
        if conditions:
            count_query = count_query.where(and_(*conditions))
        
        count_result = await session.execute(count_query)
        total = count_result.scalar() or 0
        
        # 计算分页信息
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        offset = (page - 1) * page_size
        
        # 查询数据
        query = select(Reconciliation)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # 按创建时间倒序排列
        query = query.order_by(Reconciliation.created_at.desc()).offset(offset).limit(page_size)
        
        result = await session.execute(query)
        recon_list = result.scalars().all()
        
        # 转换为响应数据
        items = []
        for recon in recon_list:
            recon_dict = {
                "id": recon.id,
                "recon_date": recon.recon_date,
                "recon_type": recon.recon_type,
                "payment_method": recon.payment_method.value if recon.payment_method else None,
                "system_total_count": recon.system_total_count,
                "system_total_amount": float(recon.system_total_amount),
                "system_refund_count": recon.system_refund_count,
                "system_refund_amount": float(recon.system_refund_amount),
                "platform_total_count": recon.platform_total_count,
                "platform_total_amount": float(recon.platform_total_amount),
                "platform_refund_count": recon.platform_refund_count,
                "platform_refund_amount": float(recon.platform_refund_amount),
                "diff_count": recon.diff_count,
                "diff_amount": float(recon.diff_amount),
                "status": recon.status.value if recon.status else None,
                "resolved_by": recon.resolved_by,
                "resolved_at": recon.resolved_at.isoformat() if recon.resolved_at else None,
                "created_at": recon.created_at.isoformat() if recon.created_at else None
            }
            items.append(recon_dict)
        
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
            detail=f"获取对账列表失败: {str(e)}"
        )


@router.get("/{recon_id}", response_model=BaseResponse)
async def get_reconciliation_detail(
    recon_id: str,
    include_details: bool = Query(True, description="是否包含对账明细"),
    session: AsyncSession = Depends(get_async_session)
) -> BaseResponse:
    """
    获取对账记录详情
    
    包含对账汇总和明细
    """
    try:
        query = select(Reconciliation)
        if include_details:
            query = query.options(selectinload(Reconciliation.details))
        
        query = query.where(Reconciliation.id == recon_id)
        
        result = await session.execute(query)
        recon = result.scalar_one_or_none()
        
        if not recon:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="对账记录不存在"
            )
        
        # 构建响应数据
        recon_data = {
            "id": recon.id,
            "recon_date": recon.recon_date,
            "recon_type": recon.recon_type,
            "payment_method": recon.payment_method.value if recon.payment_method else None,
            "system_total_count": recon.system_total_count,
            "system_total_amount": float(recon.system_total_amount),
            "system_refund_count": recon.system_refund_count,
            "system_refund_amount": float(recon.system_refund_amount),
            "platform_total_count": recon.platform_total_count,
            "platform_total_amount": float(recon.platform_total_amount),
            "platform_refund_count": recon.platform_refund_count,
            "platform_refund_amount": float(recon.platform_refund_amount),
            "diff_count": recon.diff_count,
            "diff_amount": float(recon.diff_amount),
            "status": recon.status.value if recon.status else None,
            "resolved_by": recon.resolved_by,
            "resolved_at": recon.resolved_at.isoformat() if recon.resolved_at else None,
            "resolve_remark": recon.resolve_remark,
            "created_at": recon.created_at.isoformat() if recon.created_at else None,
            "updated_at": recon.updated_at.isoformat() if recon.updated_at else None
        }
        
        # 对账明细
        if recon.details:
            recon_data["details"] = []
            for detail in recon.details:
                recon_data["details"].append({
                    "id": detail.id,
                    "order_no": detail.order_no,
                    "third_party_order_no": detail.third_party_order_no,
                    "system_amount": float(detail.system_amount) if detail.system_amount else None,
                    "system_status": detail.system_status,
                    "platform_amount": float(detail.platform_amount) if detail.platform_amount else None,
                    "platform_status": detail.platform_status,
                    "is_matched": detail.is_matched,
                    "diff_type": detail.diff_type,
                    "diff_amount": float(detail.diff_amount),
                    "diff_description": detail.diff_description,
                    "is_resolved": detail.is_resolved,
                    "resolved_by": detail.resolved_by,
                    "resolved_at": detail.resolved_at.isoformat() if detail.resolved_at else None,
                    "resolve_remark": detail.resolve_remark
                })
        
        return BaseResponse(
            code=200,
            message="获取对账详情成功",
            data=recon_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取对账详情失败: {str(e)}"
        )


@router.post("", response_model=BaseResponse)
async def create_reconciliation(
    recon_data: ReconciliationCreate,
    session: AsyncSession = Depends(get_async_session)
) -> BaseResponse:
    """
    创建对账记录
    
    1. 验证对账日期格式
    2. 统计系统订单数据
    3. 生成对账记录（平台数据需要人工或接口导入）
    """
    try:
        # 检查是否已存在对账记录
        exist_query = select(Reconciliation).where(
            and_(
                Reconciliation.recon_date == recon_data.recon_date,
                Reconciliation.recon_type == recon_data.recon_type,
                Reconciliation.payment_method == recon_data.payment_method
            )
        )
        exist_result = await session.execute(exist_query)
        exist_recon = exist_result.scalar_one_or_none()
        
        if exist_recon:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该日期和支付方式的对账记录已存在"
            )
        
        # 获取时间范围
        start_dt, end_dt = get_recon_date_range(
            recon_data.recon_date, recon_data.recon_type
        )
        
        # 统计系统订单数据
        # 总订单数和金额
        order_query = select(Order).where(
            and_(
                Order.payment_method == recon_data.payment_method,
                Order.created_at >= start_dt,
                Order.created_at <= end_dt,
                Order.payment_status != PaymentStatus.PENDING
            )
        )
        
        order_result = await session.execute(order_query)
        orders = order_result.scalars().all()
        
        # 统计
        total_count = len(orders)
        total_amount = sum(o.pay_amount for o in orders if o.pay_amount)
        refund_count = sum(1 for o in orders if o.payment_status in [
            PaymentStatus.REFUNDED, PaymentStatus.PARTIAL_REFUNDED
        ])
        refund_amount = sum(o.pay_amount for o in orders if o.payment_status in [
            PaymentStatus.REFUNDED, PaymentStatus.PARTIAL_REFUNDED
        ])
        
        # 创建对账记录
        reconciliation = Reconciliation(
            recon_date=recon_data.recon_date,
            recon_type=recon_data.recon_type,
            payment_method=recon_data.payment_method,
            system_total_count=total_count,
            system_total_amount=total_amount,
            system_refund_count=refund_count,
            system_refund_amount=refund_amount,
            platform_total_count=0,
            platform_total_amount=Decimal(0),
            platform_refund_count=0,
            platform_refund_amount=Decimal(0),
            diff_count=0,
            diff_amount=Decimal(0),
            status=ReconciliationStatus.PENDING
        )
        
        session.add(reconciliation)
        await session.flush()
        
        # 生成对账明细（基于系统订单）
        for order in orders:
            detail = ReconciliationDetail(
                recon_id=reconciliation.id,
                order_id=order.id,
                order_no=order.order_no,
                third_party_order_no=order.third_party_order_no,
                system_amount=order.pay_amount,
                system_status=order.payment_status.value if order.payment_status else None,
                is_matched=False,  # 默认未匹配，等待平台数据
                diff_amount=Decimal(0)
            )
            session.add(detail)
        
        await session.commit()
        
        return BaseResponse(
            code=200,
            message="对账记录创建成功",
            data={
                "id": reconciliation.id,
                "recon_date": reconciliation.recon_date,
                "recon_type": reconciliation.recon_type,
                "payment_method": reconciliation.payment_method.value,
                "system_total_count": total_count,
                "system_total_amount": float(total_amount),
                "status": reconciliation.status.value,
                "created_at": reconciliation.created_at.isoformat() if reconciliation.created_at else None
            }
        )
        
    except HTTPException:
        await session.rollback()
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建对账记录失败: {str(e)}"
        )


@router.post("/{recon_id}/import-platform", response_model=BaseResponse)
async def import_platform_data(
    recon_id: str,
    platform_total_count: int = Query(..., description="平台订单总数"),
    platform_total_amount: float = Query(..., description="平台总金额"),
    platform_refund_count: int = Query(0, description="平台退款订单数"),
    platform_refund_amount: float = Query(0.0, description="平台退款总金额"),
    session: AsyncSession = Depends(get_async_session)
) -> BaseResponse:
    """
    导入第三方支付平台数据
    
    模拟从支付平台导入对账数据
    """
    try:
        # 查询对账记录
        query = select(Reconciliation).options(
            selectinload(Reconciliation.details)
        ).where(Reconciliation.id == recon_id)
        
        result = await session.execute(query)
        recon = result.scalar_one_or_none()
        
        if not recon:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="对账记录不存在"
            )
        
        # 更新平台数据
        recon.platform_total_count = platform_total_count
        recon.platform_total_amount = Decimal(str(platform_total_amount))
        recon.platform_refund_count = platform_refund_count
        recon.platform_refund_amount = Decimal(str(platform_refund_amount))
        
        # 计算差异
        # 这里简化处理，实际需要逐单匹配
        system_net = recon.system_total_amount - recon.system_refund_amount
        platform_net = recon.platform_total_amount - recon.platform_refund_amount
        
        recon.diff_count = abs(recon.system_total_count - recon.platform_total_count)
        recon.diff_amount = abs(system_net - platform_net)
        
        # 更新对账状态
        if recon.diff_count == 0 and recon.diff_amount == 0:
            recon.status = ReconciliationStatus.MATCHED
            
            # 标记所有明细为匹配
            if recon.details:
                for detail in recon.details:
                    detail.is_matched = True
        else:
            recon.status = ReconciliationStatus.UNMATCHED
        
        await session.commit()
        
        return BaseResponse(
            code=200,
            message="平台数据导入成功",
            data={
                "recon_id": recon.id,
                "system_total_count": recon.system_total_count,
                "system_total_amount": float(recon.system_total_amount),
                "platform_total_count": recon.platform_total_count,
                "platform_total_amount": float(recon.platform_total_amount),
                "diff_count": recon.diff_count,
                "diff_amount": float(recon.diff_amount),
                "status": recon.status.value
            }
        )
        
    except HTTPException:
        await session.rollback()
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导入平台数据失败: {str(e)}"
        )


@router.post("/{recon_id}/resolve", response_model=BaseResponse)
async def resolve_reconciliation(
    recon_id: str,
    resolve_data: ReconciliationResolve,
    session: AsyncSession = Depends(get_async_session)
) -> BaseResponse:
    """
    处理对账差异
    
    标记对账差异为已解决
    """
    try:
        # 查询对账记录
        query = select(Reconciliation).where(Reconciliation.id == recon_id)
        result = await session.execute(query)
        recon = result.scalar_one_or_none()
        
        if not recon:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="对账记录不存在"
            )
        
        # 更新对账状态
        recon.status = ReconciliationStatus.RESOLVED
        recon.resolved_by = resolve_data.resolved_by
        recon.resolved_at = datetime.utcnow()
        recon.resolve_remark = resolve_data.resolve_remark
        
        await session.commit()
        
        return BaseResponse(
            code=200,
            message="对账差异已处理",
            data={
                "recon_id": recon.id,
                "recon_date": recon.recon_date,
                "status": ReconciliationStatus.RESOLVED.value,
                "resolved_by": recon.resolved_by,
                "resolved_at": recon.resolved_at.isoformat() if recon.resolved_at else None,
                "resolve_remark": recon.resolve_remark
            }
        )
        
    except HTTPException:
        await session.rollback()
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理对账差异失败: {str(e)}"
        )


@router.get("/details/{detail_id}/resolve", response_model=BaseResponse)
async def resolve_detail(
    detail_id: str,
    resolve_remark: str = Query(..., description="处理备注"),
    resolved_by: str = Query(..., description="处理人"),
    session: AsyncSession = Depends(get_async_session)
) -> BaseResponse:
    """
    处理单条对账明细差异
    
    标记具体的对账差异为已解决
    """
    try:
        # 查询对账明细
        query = select(ReconciliationDetail).options(
            selectinload(ReconciliationDetail.reconciliation)
        ).where(ReconciliationDetail.id == detail_id)
        
        result = await session.execute(query)
        detail = result.scalar_one_or_none()
        
        if not detail:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="对账明细不存在"
            )
        
        # 更新明细状态
        detail.is_resolved = True
        detail.resolved_by = resolved_by
        detail.resolved_at = datetime.utcnow()
        detail.resolve_remark = resolve_remark
        
        # 检查是否所有差异都已解决
        if detail.reconciliation:
            # 这里简化处理，实际需要检查所有明细
            detail.reconciliation.status = ReconciliationStatus.RESOLVED
        
        await session.commit()
        
        return BaseResponse(
            code=200,
            message="对账明细已处理",
            data={
                "detail_id": detail.id,
                "order_no": detail.order_no,
                "is_resolved": detail.is_resolved,
                "resolved_by": detail.resolved_by,
                "resolved_at": detail.resolved_at.isoformat() if detail.resolved_at else None,
                "resolve_remark": detail.resolve_remark
            }
        )
        
    except HTTPException:
        await session.rollback()
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理对账明细失败: {str(e)}"
        )
