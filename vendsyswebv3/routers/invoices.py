"""
发票管理API路由
包含发票申请、审核、开具等功能
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
from models import Invoice, Order, User
from models import InvoiceStatus, OrderStatus
from schemas import (
    InvoiceCreate, InvoiceQuery, InvoiceReview, InvoiceIssue,
    PaginatedResponse, BaseResponse
)

# 创建路由
router = APIRouter(prefix="/api/invoices", tags=["发票管理"])


@router.get("", response_model=PaginatedResponse)
async def get_invoice_list(
    query_params: InvoiceQuery = Depends(),
    session: AsyncSession = Depends(get_async_session)
) -> PaginatedResponse:
    """
    获取发票列表（分页）
    
    支持按订单ID、用户ID、发票号码、状态筛选
    """
    try:
        page = query_params.page
        page_size = query_params.page_size
        
        # 构建查询条件
        conditions = []
        
        if query_params.order_id:
            conditions.append(Invoice.order_id == query_params.order_id)
        
        if query_params.user_id:
            conditions.append(Invoice.user_id == query_params.user_id)
        
        if query_params.invoice_no:
            conditions.append(Invoice.invoice_no.ilike(f"%{query_params.invoice_no}%"))
        
        if query_params.status:
            conditions.append(Invoice.status == query_params.status)
        
        # 查询总记录数
        count_query = select(func.count(Invoice.id)).select_from(Invoice)
        if conditions:
            count_query = count_query.where(and_(*conditions))
        
        count_result = await session.execute(count_query)
        total = count_result.scalar() or 0
        
        # 计算分页信息
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        offset = (page - 1) * page_size
        
        # 查询数据（带关联）
        query = select(Invoice).options(
            selectinload(Invoice.order),
            selectinload(Invoice.user)
        )
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # 按创建时间倒序排列
        query = query.order_by(Invoice.created_at.desc()).offset(offset).limit(page_size)
        
        result = await session.execute(query)
        invoices = result.scalars().all()
        
        # 转换为响应数据
        items = []
        for invoice in invoices:
            inv_dict = {
                "id": invoice.id,
                "order_id": invoice.order_id,
                "user_id": invoice.user_id,
                "invoice_no": invoice.invoice_no,
                "invoice_type": invoice.invoice_type,
                "title_type": invoice.title_type,
                "title_name": invoice.title_name,
                "tax_no": invoice.tax_no,
                "invoice_amount": float(invoice.invoice_amount),
                "tax_amount": float(invoice.tax_amount),
                "receiver_name": invoice.receiver_name,
                "receiver_phone": invoice.receiver_phone,
                "receiver_email": invoice.receiver_email,
                "status": invoice.status.value if invoice.status else None,
                "reviewer": invoice.reviewer,
                "reviewed_at": invoice.reviewed_at.isoformat() if invoice.reviewed_at else None,
                "issuer": invoice.issuer,
                "issued_at": invoice.issued_at.isoformat() if invoice.issued_at else None,
                "invoice_url": invoice.invoice_url,
                "created_at": invoice.created_at.isoformat() if invoice.created_at else None
            }
            
            # 订单信息
            if invoice.order:
                inv_dict["order"] = {
                    "id": invoice.order.id,
                    "order_no": invoice.order.order_no,
                    "pay_amount": float(invoice.order.pay_amount),
                    "order_status": invoice.order.order_status.value if invoice.order.order_status else None,
                    "created_at": invoice.order.created_at.isoformat() if invoice.order.created_at else None
                }
            
            # 用户信息
            if invoice.user:
                inv_dict["user"] = {
                    "id": invoice.user.id,
                    "phone": invoice.user.phone,
                    "nickname": invoice.user.nickname
                }
            
            items.append(inv_dict)
        
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
            detail=f"获取发票列表失败: {str(e)}"
        )


@router.get("/{invoice_id}", response_model=BaseResponse)
async def get_invoice_detail(
    invoice_id: str,
    session: AsyncSession = Depends(get_async_session)
) -> BaseResponse:
    """
    获取发票详情
    
    包含发票信息、关联订单和用户信息
    """
    try:
        query = select(Invoice).options(
            selectinload(Invoice.order).options(
                selectinload(Order.order_items)
            ),
            selectinload(Invoice.user)
        ).where(Invoice.id == invoice_id)
        
        result = await session.execute(query)
        invoice = result.scalar_one_or_none()
        
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="发票不存在"
            )
        
        # 构建响应数据
        inv_data = {
            "id": invoice.id,
            "order_id": invoice.order_id,
            "user_id": invoice.user_id,
            "invoice_no": invoice.invoice_no,
            "invoice_type": invoice.invoice_type,
            "title_type": invoice.title_type,
            "title_name": invoice.title_name,
            "tax_no": invoice.tax_no,
            "company_address": invoice.company_address,
            "company_phone": invoice.company_phone,
            "bank_name": invoice.bank_name,
            "bank_account": invoice.bank_account,
            "invoice_content": invoice.invoice_content,
            "invoice_amount": float(invoice.invoice_amount),
            "tax_amount": float(invoice.tax_amount),
            "receiver_name": invoice.receiver_name,
            "receiver_phone": invoice.receiver_phone,
            "receiver_email": invoice.receiver_email,
            "status": invoice.status.value if invoice.status else None,
            "reviewer": invoice.reviewer,
            "review_remark": invoice.review_remark,
            "reviewed_at": invoice.reviewed_at.isoformat() if invoice.reviewed_at else None,
            "issuer": invoice.issuer,
            "issued_at": invoice.issued_at.isoformat() if invoice.issued_at else None,
            "invoice_url": invoice.invoice_url,
            "invoice_pdf_url": invoice.invoice_pdf_url,
            "reject_reason": invoice.reject_reason,
            "void_reason": invoice.void_reason,
            "voided_at": invoice.voided_at.isoformat() if invoice.voided_at else None,
            "created_at": invoice.created_at.isoformat() if invoice.created_at else None,
            "updated_at": invoice.updated_at.isoformat() if invoice.updated_at else None
        }
        
        # 订单信息
        if invoice.order:
            order = invoice.order
            inv_data["order"] = {
                "id": order.id,
                "order_no": order.order_no,
                "user_id": order.user_id,
                "machine_id": order.machine_id,
                "total_amount": float(order.total_amount),
                "pay_amount": float(order.pay_amount),
                "payment_method": order.payment_method.value if order.payment_method else None,
                "payment_status": order.payment_status.value if order.payment_status else None,
                "order_status": order.order_status.value if order.order_status else None,
                "created_at": order.created_at.isoformat() if order.created_at else None,
                "paid_at": order.paid_at.isoformat() if order.paid_at else None
            }
            
            # 订单商品明细
            if order.order_items:
                inv_data["order"]["items"] = []
                for item in order.order_items:
                    inv_data["order"]["items"].append({
                        "product_code": item.product_code,
                        "product_name": item.product_name,
                        "quantity": item.quantity,
                        "unit_price": float(item.unit_price),
                        "subtotal_amount": float(item.subtotal_amount)
                    })
        
        # 用户信息
        if invoice.user:
            inv_data["user"] = {
                "id": invoice.user.id,
                "user_code": invoice.user.user_code,
                "phone": invoice.user.phone,
                "nickname": invoice.user.nickname
            }
        
        return BaseResponse(
            code=200,
            message="获取发票详情成功",
            data=inv_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取发票详情失败: {str(e)}"
        )


@router.post("", response_model=BaseResponse)
async def create_invoice_application(
    inv_data: InvoiceCreate,
    session: AsyncSession = Depends(get_async_session)
) -> BaseResponse:
    """
    创建发票申请
    
    用户提交发票申请
    1. 验证订单存在且已完成
    2. 验证用户存在
    3. 检查是否已存在发票申请
    4. 创建发票申请记录
    """
    try:
        # 验证订单存在
        order_query = select(Order).where(Order.id == inv_data.order_id)
        order_result = await session.execute(order_query)
        order = order_result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="订单不存在"
            )
        
        # 验证订单状态（必须已支付或已完成）
        if order.order_status not in [OrderStatus.PAID, OrderStatus.DELIVERED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该订单状态不允许申请发票"
            )
        
        # 验证用户存在
        user_query = select(User).where(User.id == inv_data.user_id)
        user_result = await session.execute(user_query)
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户不存在"
            )
        
        # 检查是否已存在发票申请
        exist_query = select(Invoice).where(Invoice.order_id == inv_data.order_id)
        exist_result = await session.execute(exist_query)
        exist_inv = exist_result.scalar_one_or_none()
        
        if exist_inv:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该订单已存在发票申请"
            )
        
        # 验证企业发票需要税号
        if inv_data.title_type == "company" and not inv_data.tax_no:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="企业发票必须提供纳税人识别号"
            )
        
        # 计算发票金额不能超过订单实付金额
        invoice_amount = order.pay_amount
        
        # 创建发票申请
        invoice = Invoice(
            order_id=inv_data.order_id,
            user_id=inv_data.user_id,
            invoice_type="electronic",
            title_type=inv_data.title_type,
            title_name=inv_data.title_name,
            tax_no=inv_data.tax_no,
            company_address=inv_data.company_address,
            company_phone=inv_data.company_phone,
            bank_name=inv_data.bank_name,
            bank_account=inv_data.bank_account,
            invoice_content=inv_data.invoice_content,
            invoice_amount=invoice_amount,
            tax_amount=Decimal(0),  # 税额根据实际情况计算
            receiver_name=inv_data.receiver_name,
            receiver_phone=inv_data.receiver_phone,
            receiver_email=inv_data.receiver_email,
            status=InvoiceStatus.PENDING
        )
        
        session.add(invoice)
        await session.commit()
        
        return BaseResponse(
            code=200,
            message="发票申请提交成功",
            data={
                "id": invoice.id,
                "order_id": invoice.order_id,
                "order_no": order.order_no,
                "title_type": invoice.title_type,
                "title_name": invoice.title_name,
                "invoice_amount": float(invoice.invoice_amount),
                "status": InvoiceStatus.PENDING.value,
                "created_at": invoice.created_at.isoformat() if invoice.created_at else None
            }
        )
        
    except HTTPException:
        await session.rollback()
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建发票申请失败: {str(e)}"
        )


@router.post("/{invoice_id}/review", response_model=BaseResponse)
async def review_invoice(
    invoice_id: str,
    review_data: InvoiceReview,
    session: AsyncSession = Depends(get_async_session)
) -> BaseResponse:
    """
    审核发票申请
    
    管理员审核发票申请，通过或拒绝
    """
    try:
        # 查询发票
        query = select(Invoice).options(
            selectinload(Invoice.order)
        ).where(Invoice.id == invoice_id)
        
        result = await session.execute(query)
        invoice = result.scalar_one_or_none()
        
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="发票申请不存在"
            )
        
        # 检查状态
        if invoice.status != InvoiceStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该发票申请已处理"
            )
        
        # 更新审核信息
        invoice.reviewer = review_data.reviewer
        invoice.review_remark = review_data.review_remark
        invoice.reviewed_at = datetime.utcnow()
        
        if review_data.approved:
            # 审核通过
            invoice.status = InvoiceStatus.APPROVED
        else:
            # 审核拒绝
            invoice.status = InvoiceStatus.REJECTED
            invoice.reject_reason = review_data.review_remark
        
        await session.commit()
        
        return BaseResponse(
            code=200,
            message=f"发票申请已{'通过' if review_data.approved else '拒绝'}",
            data={
                "invoice_id": invoice.id,
                "order_id": invoice.order_id,
                "order_no": invoice.order.order_no if invoice.order else None,
                "status": invoice.status.value,
                "reviewer": invoice.reviewer,
                "review_remark": invoice.review_remark,
                "reviewed_at": invoice.reviewed_at.isoformat() if invoice.reviewed_at else None
            }
        )
        
    except HTTPException:
        await session.rollback()
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"审核发票失败: {str(e)}"
        )


@router.post("/{invoice_id}/issue", response_model=BaseResponse)
async def issue_invoice(
    invoice_id: str,
    issue_data: InvoiceIssue,
    session: AsyncSession = Depends(get_async_session)
) -> BaseResponse:
    """
    开具发票
    
    模拟发票系统开具电子发票
    """
    try:
        # 查询发票
        query = select(Invoice).options(
            selectinload(Invoice.order)
        ).where(Invoice.id == invoice_id)
        
        result = await session.execute(query)
        invoice = result.scalar_one_or_none()
        
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="发票申请不存在"
            )
        
        # 检查状态
        if invoice.status != InvoiceStatus.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该发票申请尚未审核通过"
            )
        
        # 检查发票号码是否重复
        exist_query = select(Invoice).where(
            Invoice.invoice_no == issue_data.invoice_no,
            Invoice.id != invoice_id
        )
        exist_result = await session.execute(exist_query)
        exist_inv = exist_result.scalar_one_or_none()
        
        if exist_inv:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="发票号码已存在"
            )
        
        # 更新发票信息
        invoice.invoice_no = issue_data.invoice_no
        invoice.invoice_url = issue_data.invoice_url
        invoice.invoice_pdf_url = issue_data.invoice_pdf_url
        invoice.issuer = issue_data.issuer
        invoice.issued_at = datetime.utcnow()
        invoice.status = InvoiceStatus.ISSUED
        
        await session.commit()
        
        return BaseResponse(
            code=200,
            message="发票开具成功",
            data={
                "invoice_id": invoice.id,
                "order_id": invoice.order_id,
                "invoice_no": invoice.invoice_no,
                "title_name": invoice.title_name,
                "invoice_amount": float(invoice.invoice_amount),
                "status": InvoiceStatus.ISSUED.value,
                "issuer": invoice.issuer,
                "issued_at": invoice.issued_at.isoformat() if invoice.issued_at else None,
                "invoice_url": invoice.invoice_url,
                "invoice_pdf_url": invoice.invoice_pdf_url
            }
        )
        
    except HTTPException:
        await session.rollback()
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"开具发票失败: {str(e)}"
        )


@router.post("/{invoice_id}/void", response_model=BaseResponse)
async def void_invoice(
    invoice_id: str,
    void_reason: str = Query(..., description="作废原因"),
    handled_by: str = Query(..., description="操作人"),
    session: AsyncSession = Depends(get_async_session)
) -> BaseResponse:
    """
    作废发票
    
    作废已开具的发票
    """
    try:
        # 查询发票
        query = select(Invoice).where(Invoice.id == invoice_id)
        result = await session.execute(query)
        invoice = result.scalar_one_or_none()
        
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="发票不存在"
            )
        
        # 检查状态
        if invoice.status != InvoiceStatus.ISSUED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只能作废已开具的发票"
            )
        
        # 作废发票
        invoice.status = InvoiceStatus.VOIDED
        invoice.void_reason = void_reason
        invoice.voided_at = datetime.utcnow()
        
        await session.commit()
        
        return BaseResponse(
            code=200,
            message="发票已作废",
            data={
                "invoice_id": invoice.id,
                "invoice_no": invoice.invoice_no,
                "status": InvoiceStatus.VOIDED.value,
                "void_reason": invoice.void_reason,
                "voided_at": invoice.voided_at.isoformat() if invoice.voided_at else None
            }
        )
        
    except HTTPException:
        await session.rollback()
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"作废发票失败: {str(e)}"
        )


@router.get("/check/order/{order_id}", response_model=BaseResponse)
async def check_invoice_eligibility(
    order_id: str,
    session: AsyncSession = Depends(get_async_session)
) -> BaseResponse:
    """
    检查订单是否可以申请发票
    
    返回是否可以申请、已申请状态等信息
    """
    try:
        # 查询订单
        order_query = select(Order).where(Order.id == order_id)
        order_result = await session.execute(order_query)
        order = order_result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="订单不存在"
            )
        
        # 检查是否已存在发票
        invoice_query = select(Invoice).where(Invoice.order_id == order_id)
        invoice_result = await session.execute(invoice_query)
        invoice = invoice_result.scalar_one_or_none()
        
        # 检查订单状态
        can_apply = order.order_status in [OrderStatus.PAID, OrderStatus.DELIVERED]
        
        data = {
            "order_id": order.id,
            "order_no": order.order_no,
            "order_status": order.order_status.value if order.order_status else None,
            "pay_amount": float(order.pay_amount),
            "can_apply": can_apply,
            "has_invoice": invoice is not None,
            "invoice_status": invoice.status.value if invoice else None,
            "invoice_id": invoice.id if invoice else None
        }
        
        if not can_apply and not invoice:
            data["reason"] = "订单状态不允许申请发票，需订单已支付或已完成"
        
        return BaseResponse(
            code=200,
            message="查询成功",
            data=data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"检查发票资格失败: {str(e)}"
        )
