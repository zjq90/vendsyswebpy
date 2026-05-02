"""
API数据模型定义
使用Pydantic进行请求和响应数据验证
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from enum import Enum

# ==================== 枚举类型（用于API） ====================

class PaymentMethod(str, Enum):
    """支付方式"""
    WECHAT = "wechat"
    ALIPAY = "alipay"
    CASH = "cash"
    CARD = "card"


class PaymentStatus(str, Enum):
    """支付状态"""
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDING = "refunding"
    REFUNDED = "refunded"
    PARTIAL_REFUNDED = "partial_refunded"


class DeliveryStatus(str, Enum):
    """出货状态"""
    PENDING = "pending"
    DELIVERING = "delivering"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    RETURNED = "returned"


class OrderStatus(str, Enum):
    """订单状态"""
    CREATED = "created"
    PAID = "paid"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    ABNORMAL = "abnormal"


class AbnormalType(str, Enum):
    """异常类型"""
    PAID_NO_DELIVERY = "paid_no_delivery"
    DELIVERY_FAILED = "delivery_failed"
    DUPLICATE_PAYMENT = "duplicate_payment"
    OVER_PAYMENT = "over_payment"
    SYSTEM_ERROR = "system_error"
    OTHER = "other"


class AbnormalStatus(str, Enum):
    """异常处理状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    REFUND_APPROVED = "refund_approved"
    REFUNDED = "refunded"
    REDISPATCH_APPROVED = "redispatch_approved"
    REDISPATCHED = "redispatched"
    RESOLVED = "resolved"
    CLOSED = "closed"


class ReconciliationStatus(str, Enum):
    """对账状态"""
    PENDING = "pending"
    MATCHED = "matched"
    UNMATCHED = "unmatched"
    RESOLVED = "resolved"


class InvoiceStatus(str, Enum):
    """发票状态"""
    PENDING = "pending"
    APPROVED = "approved"
    ISSUED = "issued"
    REJECTED = "rejected"
    VOIDED = "voided"


# ==================== 基础响应模型 ====================

class BaseResponse(BaseModel):
    """基础响应模型"""
    code: int = Field(default=200, description="状态码")
    message: str = Field(default="success", description="消息")
    data: Optional[dict] = Field(default=None, description="数据")


class PaginatedResponse(BaseModel):
    """分页响应模型"""
    total: int = Field(description="总记录数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页数量")
    total_pages: int = Field(description="总页数")
    items: List[dict] = Field(description="数据列表")


# ==================== 售货机相关模型 ====================

class VendingMachineBase(BaseModel):
    """售货机基础模型"""
    machine_code: str = Field(..., min_length=1, max_length=50, description="售货机编号")
    machine_name: str = Field(..., min_length=1, max_length=100, description="售货机名称")
    location: Optional[str] = Field(None, max_length=200, description="安装位置")
    address: Optional[str] = Field(None, max_length=200, description="详细地址")
    status: Optional[str] = Field(default="active", description="状态")


class VendingMachineCreate(VendingMachineBase):
    """创建售货机模型"""
    pass


class VendingMachineUpdate(BaseModel):
    """更新售货机模型"""
    machine_name: Optional[str] = Field(None, min_length=1, max_length=100)
    location: Optional[str] = Field(None, max_length=200)
    address: Optional[str] = Field(None, max_length=200)
    status: Optional[str] = None


class VendingMachineResponse(VendingMachineBase):
    """售货机响应模型"""
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== 商品相关模型 ====================

class ProductBase(BaseModel):
    """商品基础模型"""
    product_code: str = Field(..., min_length=1, max_length=50, description="商品编码")
    product_name: str = Field(..., min_length=1, max_length=100, description="商品名称")
    category: Optional[str] = Field(None, max_length=50, description="商品分类")
    price: Decimal = Field(..., gt=0, description="单价")
    cost_price: Optional[Decimal] = Field(None, gt=0, description="成本价")
    image_url: Optional[str] = Field(None, max_length=500, description="商品图片URL")
    description: Optional[str] = Field(None, description="商品描述")
    status: Optional[str] = Field(default="active", description="状态")


class ProductCreate(ProductBase):
    """创建商品模型"""
    pass


class ProductUpdate(BaseModel):
    """更新商品模型"""
    product_name: Optional[str] = Field(None, min_length=1, max_length=100)
    category: Optional[str] = Field(None, max_length=50)
    price: Optional[Decimal] = Field(None, gt=0)
    cost_price: Optional[Decimal] = Field(None, gt=0)
    image_url: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    status: Optional[str] = None


class ProductResponse(ProductBase):
    """商品响应模型"""
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== 用户相关模型 ====================

class UserBase(BaseModel):
    """用户基础模型"""
    user_code: str = Field(..., min_length=1, max_length=50, description="用户编号")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    nickname: Optional[str] = Field(None, max_length=100, description="昵称")
    avatar_url: Optional[str] = Field(None, max_length=500, description="头像URL")
    status: Optional[str] = Field(default="active", description="状态")


class UserCreate(UserBase):
    """创建用户模型"""
    wechat_openid: Optional[str] = None
    alipay_user_id: Optional[str] = None


class UserUpdate(BaseModel):
    """更新用户模型"""
    phone: Optional[str] = Field(None, max_length=20)
    nickname: Optional[str] = Field(None, max_length=100)
    avatar_url: Optional[str] = Field(None, max_length=500)
    status: Optional[str] = None


class UserResponse(UserBase):
    """用户响应模型"""
    id: str
    wechat_openid: Optional[str] = None
    alipay_user_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== 订单相关模型 ====================

class OrderItemBase(BaseModel):
    """订单明细基础模型"""
    product_id: str = Field(..., description="商品ID")
    quantity: int = Field(..., ge=1, description="购买数量")


class OrderItemCreate(OrderItemBase):
    """创建订单明细模型"""
    pass


class OrderItemResponse(BaseModel):
    """订单明细响应模型"""
    id: str
    order_id: str
    product_id: str
    product_code: str
    product_name: str
    quantity: int
    unit_price: Decimal
    subtotal_amount: Decimal
    delivery_status: DeliveryStatus
    delivered_quantity: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrderBase(BaseModel):
    """订单基础模型"""
    machine_id: str = Field(..., description="售货机ID")
    user_id: Optional[str] = Field(None, description="用户ID")
    remark: Optional[str] = Field(None, description="订单备注")


class OrderCreate(OrderBase):
    """创建订单模型"""
    items: List[OrderItemCreate] = Field(..., min_length=1, description="商品明细列表")
    payment_method: PaymentMethod = Field(default=PaymentMethod.WECHAT, description="支付方式")


class OrderQuery(BaseModel):
    """订单查询参数模型"""
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=10, ge=1, le=100, description="每页数量")
    order_no: Optional[str] = Field(None, description="订单号")
    user_id: Optional[str] = Field(None, description="用户ID")
    machine_id: Optional[str] = Field(None, description="售货机ID")
    order_status: Optional[OrderStatus] = Field(None, description="订单状态")
    payment_status: Optional[PaymentStatus] = Field(None, description="支付状态")
    payment_method: Optional[PaymentMethod] = Field(None, description="支付方式")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")


class OrderResponse(BaseModel):
    """订单响应模型"""
    id: str
    order_no: str
    user_id: Optional[str]
    machine_id: Optional[str]
    total_amount: Decimal
    discount_amount: Decimal
    pay_amount: Decimal
    payment_method: PaymentMethod
    payment_status: PaymentStatus
    third_party_order_no: Optional[str]
    paid_at: Optional[datetime]
    delivery_status: DeliveryStatus
    delivered_at: Optional[datetime]
    order_status: OrderStatus
    remark: Optional[str]
    cancel_reason: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    # 关联信息
    user: Optional[UserResponse] = None
    machine: Optional[VendingMachineResponse] = None
    items: Optional[List[OrderItemResponse]] = None

    class Config:
        from_attributes = True


class OrderStatusUpdate(BaseModel):
    """订单状态更新模型"""
    order_status: Optional[OrderStatus] = None
    payment_status: Optional[PaymentStatus] = None
    delivery_status: Optional[DeliveryStatus] = None
    remark: Optional[str] = None


# ==================== 异常订单相关模型 ====================

class AbnormalOrderBase(BaseModel):
    """异常订单基础模型"""
    abnormal_type: AbnormalType = Field(..., description="异常类型")
    abnormal_description: Optional[str] = Field(None, description="异常描述")


class AbnormalOrderCreate(AbnormalOrderBase):
    """创建异常订单模型"""
    order_id: str = Field(..., description="订单ID")


class AbnormalOrderQuery(BaseModel):
    """异常订单查询参数模型"""
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=10, ge=1, le=100, description="每页数量")
    order_id: Optional[str] = Field(None, description="订单ID")
    abnormal_type: Optional[AbnormalType] = Field(None, description="异常类型")
    status: Optional[AbnormalStatus] = Field(None, description="处理状态")


class AbnormalOrderRefund(BaseModel):
    """异常订单退款申请模型"""
    refund_amount: Decimal = Field(..., gt=0, description="退款金额")
    refund_reason: str = Field(..., min_length=1, description="退款原因")
    refund_remark: Optional[str] = Field(None, description="退款备注")
    handled_by: str = Field(..., description="处理人")


class AbnormalOrderRedispatch(BaseModel):
    """异常订单补发申请模型"""
    redispatch_machine_id: Optional[str] = Field(None, description="补发售货机ID")
    redispatch_remark: Optional[str] = Field(None, description="补发备注")
    handled_by: str = Field(..., description="处理人")


class AbnormalOrderResponse(BaseModel):
    """异常订单响应模型"""
    id: str
    order_id: str
    abnormal_type: AbnormalType
    abnormal_description: Optional[str]
    abnormal_time: Optional[datetime]
    status: AbnormalStatus
    refund_amount: Optional[Decimal]
    refund_reason: Optional[str]
    refund_approved_at: Optional[datetime]
    refund_completed_at: Optional[datetime]
    refund_remark: Optional[str]
    redispatch_approved_at: Optional[datetime]
    redispatch_completed_at: Optional[datetime]
    redispatch_machine_id: Optional[str]
    redispatch_remark: Optional[str]
    handled_by: Optional[str]
    handler_remark: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    # 关联订单信息
    order: Optional[OrderResponse] = None

    class Config:
        from_attributes = True


# ==================== 对账相关模型 ====================

class ReconciliationBase(BaseModel):
    """对账基础模型"""
    recon_date: str = Field(..., description="对账日期: YYYY-MM-DD 或 YYYY-MM")
    recon_type: str = Field(default="daily", description="对账类型: daily-每日, monthly-每月")
    payment_method: PaymentMethod = Field(..., description="支付方式")


class ReconciliationCreate(ReconciliationBase):
    """创建对账记录模型"""
    pass


class ReconciliationQuery(BaseModel):
    """对账查询参数模型"""
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=10, ge=1, le=100, description="每页数量")
    recon_date: Optional[str] = Field(None, description="对账日期")
    recon_type: Optional[str] = Field(None, description="对账类型")
    payment_method: Optional[PaymentMethod] = Field(None, description="支付方式")
    status: Optional[ReconciliationStatus] = Field(None, description="对账状态")


class ReconciliationDetailResponse(BaseModel):
    """对账明细响应模型"""
    id: str
    recon_id: str
    order_id: Optional[str]
    order_no: str
    third_party_order_no: Optional[str]
    system_amount: Optional[Decimal]
    system_status: Optional[str]
    platform_amount: Optional[Decimal]
    platform_status: Optional[str]
    is_matched: bool
    diff_type: Optional[str]
    diff_amount: Decimal
    diff_description: Optional[str]
    is_resolved: bool
    resolved_by: Optional[str]
    resolved_at: Optional[datetime]
    resolve_remark: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReconciliationResponse(BaseModel):
    """对账响应模型"""
    id: str
    recon_date: str
    recon_type: str
    payment_method: PaymentMethod
    system_total_count: int
    system_total_amount: Decimal
    system_refund_count: int
    system_refund_amount: Decimal
    platform_total_count: int
    platform_total_amount: Decimal
    platform_refund_count: int
    platform_refund_amount: Decimal
    diff_count: int
    diff_amount: Decimal
    status: ReconciliationStatus
    resolved_by: Optional[str]
    resolved_at: Optional[datetime]
    resolve_remark: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    details: Optional[List[ReconciliationDetailResponse]] = None

    class Config:
        from_attributes = True


class ReconciliationResolve(BaseModel):
    """对账差异处理模型"""
    resolve_remark: str = Field(..., description="处理备注")
    resolved_by: str = Field(..., description="处理人")


# ==================== 发票相关模型 ====================

class InvoiceBase(BaseModel):
    """发票基础模型"""
    title_type: str = Field(..., description="抬头类型: personal-个人, company-企业")
    title_name: str = Field(..., min_length=1, max_length=200, description="发票抬头名称")
    tax_no: Optional[str] = Field(None, max_length=50, description="纳税人识别号")
    company_address: Optional[str] = Field(None, max_length=200, description="企业地址")
    company_phone: Optional[str] = Field(None, max_length=50, description="企业电话")
    bank_name: Optional[str] = Field(None, max_length=100, description="开户银行")
    bank_account: Optional[str] = Field(None, max_length=50, description="银行账号")
    invoice_content: Optional[str] = Field(default="商品明细", max_length=200, description="发票内容")
    receiver_name: Optional[str] = Field(None, max_length=100, description="收票人姓名")
    receiver_phone: Optional[str] = Field(None, max_length=20, description="收票人电话")
    receiver_email: Optional[str] = Field(None, max_length=100, description="收票人邮箱")


class InvoiceCreate(InvoiceBase):
    """创建发票申请模型"""
    order_id: str = Field(..., description="订单ID")
    user_id: str = Field(..., description="用户ID")


class InvoiceQuery(BaseModel):
    """发票查询参数模型"""
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=10, ge=1, le=100, description="每页数量")
    order_id: Optional[str] = Field(None, description="订单ID")
    user_id: Optional[str] = Field(None, description="用户ID")
    invoice_no: Optional[str] = Field(None, description="发票号码")
    status: Optional[InvoiceStatus] = Field(None, description="发票状态")


class InvoiceReview(BaseModel):
    """发票审核模型"""
    approved: bool = Field(..., description="是否通过")
    review_remark: Optional[str] = Field(None, description="审核备注")
    reviewer: str = Field(..., description="审核人")


class InvoiceIssue(BaseModel):
    """发票开具模型"""
    invoice_no: str = Field(..., description="发票号码")
    invoice_url: Optional[str] = Field(None, description="电子发票URL")
    invoice_pdf_url: Optional[str] = Field(None, description="发票PDF下载URL")
    issuer: str = Field(..., description="开具人")


class InvoiceResponse(BaseModel):
    """发票响应模型"""
    id: str
    order_id: str
    user_id: str
    invoice_no: Optional[str]
    invoice_type: str
    title_type: str
    title_name: str
    tax_no: Optional[str]
    company_address: Optional[str]
    company_phone: Optional[str]
    bank_name: Optional[str]
    bank_account: Optional[str]
    invoice_content: str
    invoice_amount: Decimal
    tax_amount: Decimal
    receiver_name: Optional[str]
    receiver_phone: Optional[str]
    receiver_email: Optional[str]
    status: InvoiceStatus
    reviewer: Optional[str]
    review_remark: Optional[str]
    reviewed_at: Optional[datetime]
    issuer: Optional[str]
    issued_at: Optional[datetime]
    invoice_url: Optional[str]
    invoice_pdf_url: Optional[str]
    reject_reason: Optional[str]
    void_reason: Optional[str]
    voided_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    # 关联信息
    order: Optional[OrderResponse] = None
    user: Optional[UserResponse] = None

    class Config:
        from_attributes = True


# ==================== 统计模型 ====================

class OrderStatistics(BaseModel):
    """订单统计模型"""
    total_orders: int = Field(default=0, description="总订单数")
    total_amount: Decimal = Field(default=0, description="总金额")
    pending_payment: int = Field(default=0, description="待支付")
    paid: int = Field(default=0, description="已支付")
    delivered: int = Field(default=0, description="已完成")
    cancelled: int = Field(default=0, description="已取消")
    refunded: int = Field(default=0, description="已退款")
    abnormal: int = Field(default=0, description="异常订单")


class AbnormalStatistics(BaseModel):
    """异常订单统计模型"""
    total_abnormal: int = Field(default=0, description="异常订单总数")
    pending: int = Field(default=0, description="待处理")
    resolved: int = Field(default=0, description="已解决")
    paid_no_delivery: int = Field(default=0, description="支付成功未出货")
    delivery_failed: int = Field(default=0, description="出货失败")
    duplicate_payment: int = Field(default=0, description="重复扣款")
    other: int = Field(default=0, description="其他异常")
