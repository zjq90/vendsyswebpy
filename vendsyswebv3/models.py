"""
数据库模型定义
包含订单、异常订单、对账、发票等核心业务模型
"""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, 
    Text, ForeignKey, Enum as SQLEnum, DECIMAL
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

# 创建基础模型类
Base = declarative_base()


# ==================== 枚举类型定义 ====================

class PaymentMethod(str, enum.Enum):
    """支付方式枚举"""
    WECHAT = "wechat"  # 微信支付
    ALIPAY = "alipay"  # 支付宝
    CASH = "cash"  # 现金
    CARD = "card"  # 银行卡


class PaymentStatus(str, enum.Enum):
    """支付状态枚举"""
    PENDING = "pending"  # 待支付
    PAID = "paid"  # 已支付
    FAILED = "failed"  # 支付失败
    REFUNDING = "refunding"  # 退款中
    REFUNDED = "refunded"  # 已退款
    PARTIAL_REFUNDED = "partial_refunded"  # 部分退款


class DeliveryStatus(str, enum.Enum):
    """取货/出货状态枚举"""
    PENDING = "pending"  # 待出货
    DELIVERING = "delivering"  # 出货中
    SUCCESS = "success"  # 出货成功
    FAILED = "failed"  # 出货失败
    PARTIAL = "partial"  # 部分出货
    RETURNED = "returned"  # 已退回


class OrderStatus(str, enum.Enum):
    """订单状态枚举"""
    CREATED = "created"  # 已创建
    PAID = "paid"  # 已支付
    DELIVERED = "delivered"  # 已完成
    CANCELLED = "cancelled"  # 已取消
    REFUNDED = "refunded"  # 已退款
    ABNORMAL = "abnormal"  # 异常订单


class AbnormalType(str, enum.Enum):
    """异常订单类型枚举"""
    PAID_NO_DELIVERY = "paid_no_delivery"  # 支付成功但未出货
    DELIVERY_FAILED = "delivery_failed"  # 出货失败
    DUPLICATE_PAYMENT = "duplicate_payment"  # 重复扣款
    OVER_PAYMENT = "over_payment"  # 多付
    SYSTEM_ERROR = "system_error"  # 系统异常
    OTHER = "other"  # 其他异常


class AbnormalStatus(str, enum.Enum):
    """异常订单处理状态枚举"""
    PENDING = "pending"  # 待处理
    PROCESSING = "processing"  # 处理中
    REFUND_APPROVED = "refund_approved"  # 退款已批准
    REFUNDED = "refunded"  # 已退款
    REDISPATCH_APPROVED = "redispatch_approved"  # 补发已批准
    REDISPATCHED = "redispatched"  # 已补发
    RESOLVED = "resolved"  # 已解决
    CLOSED = "closed"  # 已关闭


class ReconciliationStatus(str, enum.Enum):
    """对账状态枚举"""
    PENDING = "pending"  # 待对账
    MATCHED = "matched"  # 已匹配
    UNMATCHED = "unmatched"  # 有差异
    RESOLVED = "resolved"  # 差异已解决


class InvoiceStatus(str, enum.Enum):
    """发票状态枚举"""
    PENDING = "pending"  # 待审核
    APPROVED = "approved"  # 已审核
    ISSUED = "issued"  # 已开具
    REJECTED = "rejected"  # 已拒绝
    VOIDED = "voided"  # 已作废


# ==================== 数据库模型定义 ====================

def generate_uuid() -> str:
    """生成UUID字符串"""
    return str(uuid.uuid4()).replace("-", "")


class VendingMachine(Base):
    """
    自动售货机信息表
    存储售货机的基本信息
    """
    __tablename__ = "vending_machines"
    
    id = Column(String(32), primary_key=True, default=generate_uuid)
    machine_code = Column(String(50), unique=True, nullable=False, comment="售货机编号")
    machine_name = Column(String(100), nullable=False, comment="售货机名称")
    location = Column(String(200), comment="安装位置")
    address = Column(String(200), comment="详细地址")
    status = Column(String(50), default="active", comment="状态: active-正常, maintenance-维护, offline-离线")
    
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关联关系
    orders = relationship("Order", back_populates="machine")
    
    def __repr__(self):
        return f"<VendingMachine {self.machine_code} - {self.machine_name}>"


class Product(Base):
    """
    商品信息表
    存储在售商品的基本信息
    """
    __tablename__ = "products"
    
    id = Column(String(32), primary_key=True, default=generate_uuid)
    product_code = Column(String(50), unique=True, nullable=False, comment="商品编码")
    product_name = Column(String(100), nullable=False, comment="商品名称")
    category = Column(String(50), comment="商品分类")
    price = Column(DECIMAL(10, 2), nullable=False, comment="单价(元)")
    cost_price = Column(DECIMAL(10, 2), comment="成本价(元)")
    image_url = Column(String(500), comment="商品图片URL")
    description = Column(Text, comment="商品描述")
    status = Column(String(50), default="active", comment="状态: active-上架, inactive-下架")
    
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关联关系
    order_items = relationship("OrderItem", back_populates="product")
    
    def __repr__(self):
        return f"<Product {self.product_code} - {self.product_name}>"


class User(Base):
    """
    用户信息表
    存储购买用户的基本信息
    """
    __tablename__ = "users"
    
    id = Column(String(32), primary_key=True, default=generate_uuid)
    user_code = Column(String(50), unique=True, nullable=False, comment="用户编号")
    phone = Column(String(20), unique=True, comment="手机号")
    nickname = Column(String(100), comment="昵称")
    avatar_url = Column(String(500), comment="头像URL")
    
    # 微信相关
    wechat_openid = Column(String(100), unique=True, comment="微信OpenID")
    wechat_unionid = Column(String(100), comment="微信UnionID")
    
    # 支付宝相关
    alipay_user_id = Column(String(100), unique=True, comment="支付宝用户ID")
    
    status = Column(String(50), default="active", comment="状态: active-正常, blocked-禁用")
    
    created_at = Column(DateTime, default=datetime.utcnow, comment="注册时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关联关系
    orders = relationship("Order", back_populates="user")
    invoices = relationship("Invoice", back_populates="user")
    
    def __repr__(self):
        return f"<User {self.user_code} - {self.nickname or self.phone}>"


class Order(Base):
    """
    订单主表
    存储订单的核心信息
    """
    __tablename__ = "orders"
    
    id = Column(String(32), primary_key=True, default=generate_uuid)
    order_no = Column(String(50), unique=True, nullable=False, comment="订单号")
    user_id = Column(String(32), ForeignKey("users.id"), comment="用户ID")
    machine_id = Column(String(32), ForeignKey("vending_machines.id"), comment="售货机ID")
    
    # 订单金额信息
    total_amount = Column(DECIMAL(10, 2), nullable=False, comment="订单总金额(元)")
    discount_amount = Column(DECIMAL(10, 2), default=0, comment="优惠金额(元)")
    pay_amount = Column(DECIMAL(10, 2), nullable=False, comment="实付金额(元)")
    
    # 支付信息
    payment_method = Column(SQLEnum(PaymentMethod), default=PaymentMethod.WECHAT, comment="支付方式")
    payment_status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING, comment="支付状态")
    third_party_order_no = Column(String(100), comment="第三方支付平台订单号")
    paid_at = Column(DateTime, comment="支付时间")
    
    # 取货/出货信息
    delivery_status = Column(SQLEnum(DeliveryStatus), default=DeliveryStatus.PENDING, comment="出货状态")
    delivered_at = Column(DateTime, comment="出货完成时间")
    delivery_remark = Column(Text, comment="出货备注")
    
    # 订单状态
    order_status = Column(SQLEnum(OrderStatus), default=OrderStatus.CREATED, comment="订单状态")
    
    # 其他信息
    remark = Column(Text, comment="订单备注")
    cancel_reason = Column(Text, comment="取消原因")
    
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关联关系
    user = relationship("User", back_populates="orders")
    machine = relationship("VendingMachine", back_populates="orders")
    order_items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    abnormal_order = relationship("AbnormalOrder", back_populates="order", uselist=False)
    invoice = relationship("Invoice", back_populates="order", uselist=False)
    
    def __repr__(self):
        return f"<Order {self.order_no} - {self.order_status.value}>"


class OrderItem(Base):
    """
    订单明细表
    存储订单中的商品明细
    """
    __tablename__ = "order_items"
    
    id = Column(String(32), primary_key=True, default=generate_uuid)
    order_id = Column(String(32), ForeignKey("orders.id"), nullable=False, comment="订单ID")
    product_id = Column(String(32), ForeignKey("products.id"), nullable=False, comment="商品ID")
    
    # 商品信息快照（避免商品信息变更影响历史订单）
    product_code = Column(String(50), nullable=False, comment="商品编码")
    product_name = Column(String(100), nullable=False, comment="商品名称")
    
    # 数量和金额
    quantity = Column(Integer, nullable=False, default=1, comment="购买数量")
    unit_price = Column(DECIMAL(10, 2), nullable=False, comment="单价(元)")
    subtotal_amount = Column(DECIMAL(10, 2), nullable=False, comment="小计金额(元)")
    
    # 出货状态
    delivery_status = Column(SQLEnum(DeliveryStatus), default=DeliveryStatus.PENDING, comment="出货状态")
    delivered_quantity = Column(Integer, default=0, comment="已出货数量")
    
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关联关系
    order = relationship("Order", back_populates="order_items")
    product = relationship("Product", back_populates="order_items")
    
    def __repr__(self):
        return f"<OrderItem {self.product_name} x {self.quantity}>"


class AbnormalOrder(Base):
    """
    异常订单表
    存储异常订单的处理信息
    """
    __tablename__ = "abnormal_orders"
    
    id = Column(String(32), primary_key=True, default=generate_uuid)
    order_id = Column(String(32), ForeignKey("orders.id"), unique=True, nullable=False, comment="订单ID")
    
    # 异常信息
    abnormal_type = Column(SQLEnum(AbnormalType), nullable=False, comment="异常类型")
    abnormal_description = Column(Text, comment="异常描述")
    abnormal_time = Column(DateTime, default=datetime.utcnow, comment="异常发生时间")
    
    # 处理状态
    status = Column(SQLEnum(AbnormalStatus), default=AbnormalStatus.PENDING, comment="处理状态")
    
    # 退款信息
    refund_amount = Column(DECIMAL(10, 2), comment="退款金额(元)")
    refund_reason = Column(Text, comment="退款原因")
    refund_approved_at = Column(DateTime, comment="退款批准时间")
    refund_completed_at = Column(DateTime, comment="退款完成时间")
    refund_remark = Column(Text, comment="退款备注")
    
    # 补发信息
    redispatch_approved_at = Column(DateTime, comment="补发批准时间")
    redispatch_completed_at = Column(DateTime, comment="补发完成时间")
    redispatch_machine_id = Column(String(32), comment="补发售货机ID")
    redispatch_remark = Column(Text, comment="补发备注")
    
    # 处理人员信息
    handled_by = Column(String(100), comment="处理人")
    handler_remark = Column(Text, comment="处理人备注")
    
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关联关系
    order = relationship("Order", back_populates="abnormal_order")
    
    def __repr__(self):
        return f"<AbnormalOrder {self.abnormal_type.value} - {self.status.value}>"


class Reconciliation(Base):
    """
    对账主表
    存储每日/每月的对账汇总信息
    """
    __tablename__ = "reconciliations"
    
    id = Column(String(32), primary_key=True, default=generate_uuid)
    recon_date = Column(String(20), nullable=False, comment="对账日期: YYYY-MM-DD 或 YYYY-MM")
    recon_type = Column(String(20), nullable=False, comment="对账类型: daily-每日, monthly-每月")
    payment_method = Column(SQLEnum(PaymentMethod), nullable=False, comment="支付方式")
    
    # 系统数据
    system_total_count = Column(Integer, default=0, comment="系统订单总数")
    system_total_amount = Column(DECIMAL(10, 2), default=0, comment="系统总金额(元)")
    system_refund_count = Column(Integer, default=0, comment="系统退款订单数")
    system_refund_amount = Column(DECIMAL(10, 2), default=0, comment="系统退款总金额(元)")
    
    # 第三方平台数据
    platform_total_count = Column(Integer, default=0, comment="平台订单总数")
    platform_total_amount = Column(DECIMAL(10, 2), default=0, comment="平台总金额(元)")
    platform_refund_count = Column(Integer, default=0, comment="平台退款订单数")
    platform_refund_amount = Column(DECIMAL(10, 2), default=0, comment="平台退款总金额(元)")
    
    # 差异数据
    diff_count = Column(Integer, default=0, comment="差异订单数")
    diff_amount = Column(DECIMAL(10, 2), default=0, comment="差异金额(元)")
    
    # 对账状态
    status = Column(SQLEnum(ReconciliationStatus), default=ReconciliationStatus.PENDING, comment="对账状态")
    
    # 处理信息
    resolved_by = Column(String(100), comment="差异处理人")
    resolved_at = Column(DateTime, comment="差异解决时间")
    resolve_remark = Column(Text, comment="差异处理备注")
    
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关联关系
    details = relationship("ReconciliationDetail", back_populates="reconciliation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Reconciliation {self.recon_date} - {self.payment_method.value}>"


class ReconciliationDetail(Base):
    """
    对账明细表
    存储每条订单的对账明细
    """
    __tablename__ = "reconciliation_details"
    
    id = Column(String(32), primary_key=True, default=generate_uuid)
    recon_id = Column(String(32), ForeignKey("reconciliations.id"), nullable=False, comment="对账主表ID")
    order_id = Column(String(32), ForeignKey("orders.id"), comment="订单ID")
    
    # 订单信息
    order_no = Column(String(50), nullable=False, comment="订单号")
    third_party_order_no = Column(String(100), comment="第三方订单号")
    
    # 系统数据
    system_amount = Column(DECIMAL(10, 2), comment="系统金额(元)")
    system_status = Column(String(50), comment="系统状态")
    
    # 平台数据
    platform_amount = Column(DECIMAL(10, 2), comment="平台金额(元)")
    platform_status = Column(String(50), comment="平台状态")
    
    # 对账结果
    is_matched = Column(Boolean, default=False, comment="是否匹配")
    diff_type = Column(String(50), comment="差异类型: amount_diff-金额差异, status_diff-状态差异, missing_in_system-系统缺失, missing_in_platform-平台缺失")
    diff_amount = Column(DECIMAL(10, 2), default=0, comment="差异金额(元)")
    diff_description = Column(Text, comment="差异描述")
    
    # 处理状态
    is_resolved = Column(Boolean, default=False, comment="是否已解决")
    resolved_by = Column(String(100), comment="处理人")
    resolved_at = Column(DateTime, comment="解决时间")
    resolve_remark = Column(Text, comment="解决备注")
    
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关联关系
    reconciliation = relationship("Reconciliation", back_populates="details")
    
    def __repr__(self):
        return f"<ReconciliationDetail {self.order_no} - matched:{self.is_matched}>"


class Invoice(Base):
    """
    发票表
    存储发票申请和开具信息
    """
    __tablename__ = "invoices"
    
    id = Column(String(32), primary_key=True, default=generate_uuid)
    order_id = Column(String(32), ForeignKey("orders.id"), unique=True, nullable=False, comment="订单ID")
    user_id = Column(String(32), ForeignKey("users.id"), nullable=False, comment="用户ID")
    invoice_no = Column(String(50), unique=True, comment="发票号码")
    
    # 发票类型
    invoice_type = Column(String(50), default="electronic", comment="发票类型: electronic-电子发票, paper-纸质发票")
    
    # 发票抬头信息
    title_type = Column(String(50), nullable=False, comment="抬头类型: personal-个人, company-企业")
    title_name = Column(String(200), nullable=False, comment="发票抬头名称")
    tax_no = Column(String(50), comment="纳税人识别号(企业)")
    
    # 企业地址电话开户行
    company_address = Column(String(200), comment="企业地址")
    company_phone = Column(String(50), comment="企业电话")
    bank_name = Column(String(100), comment="开户银行")
    bank_account = Column(String(50), comment="银行账号")
    
    # 发票内容
    invoice_content = Column(String(200), default="商品明细", comment="发票内容")
    invoice_amount = Column(DECIMAL(10, 2), nullable=False, comment="发票金额(元)")
    tax_amount = Column(DECIMAL(10, 2), default=0, comment="税额(元)")
    
    # 收票信息
    receiver_name = Column(String(100), comment="收票人姓名")
    receiver_phone = Column(String(20), comment="收票人电话")
    receiver_email = Column(String(100), comment="收票人邮箱")
    
    # 状态
    status = Column(SQLEnum(InvoiceStatus), default=InvoiceStatus.PENDING, comment="发票状态")
    
    # 审核信息
    reviewer = Column(String(100), comment="审核人")
    review_remark = Column(Text, comment="审核备注")
    reviewed_at = Column(DateTime, comment="审核时间")
    
    # 开具信息
    issuer = Column(String(100), comment="开具人")
    issued_at = Column(DateTime, comment="开具时间")
    invoice_url = Column(String(500), comment="电子发票URL")
    invoice_pdf_url = Column(String(500), comment="发票PDF下载URL")
    
    # 拒收/作废信息
    reject_reason = Column(Text, comment="拒绝原因")
    void_reason = Column(Text, comment="作废原因")
    voided_at = Column(DateTime, comment="作废时间")
    
    created_at = Column(DateTime, default=datetime.utcnow, comment="申请时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关联关系
    order = relationship("Order", back_populates="invoice")
    user = relationship("User", back_populates="invoices")
    
    def __repr__(self):
        return f"<Invoice {self.invoice_no or '申请中'} - {self.status.value}>"
