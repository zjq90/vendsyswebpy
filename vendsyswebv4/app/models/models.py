"""
自动售后机数据统计与分析系统 - 数据模型
定义所有数据库表结构
"""
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import String, Integer, Float, DateTime, Date, Boolean, ForeignKey, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Device(Base):
    """
    设备表 - 存储自动售货机设备基本信息
    """
    __tablename__ = "devices"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="设备ID")
    device_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="设备编号")
    device_name: Mapped[str] = mapped_column(String(100), nullable=False, comment="设备名称")
    location: Mapped[str] = mapped_column(String(200), nullable=False, comment="设备位置")
    status: Mapped[str] = mapped_column(String(20), default="normal", comment="设备状态: normal-正常, maintenance-维护, offline-离线")
    
    # 设备规格信息
    capacity: Mapped[int] = mapped_column(Integer, default=0, comment="总容量(商品数)")
    slot_count: Mapped[int] = mapped_column(Integer, default=0, comment="货道数量")
    
    # 时间字段
    install_date: Mapped[date] = mapped_column(Date, nullable=True, comment="安装日期")
    last_maintenance_date: Mapped[date] = mapped_column(Date, nullable=True, comment="上次维护日期")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    
    # 关系
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="device")
    maintenances: Mapped[list["Maintenance"]] = relationship("Maintenance", back_populates="device")
    inventories: Mapped[list["Inventory"]] = relationship("Inventory", back_populates="device")
    
    def __repr__(self):
        return f"<Device {self.device_code} - {self.device_name}>"


class Product(Base):
    """
    商品表 - 存储商品基本信息
    """
    __tablename__ = "products"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="商品ID")
    product_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="商品编码")
    product_name: Mapped[str] = mapped_column(String(100), nullable=False, comment="商品名称")
    category: Mapped[str] = mapped_column(String(50), nullable=True, comment="商品分类: 饮料、零食、日用品等")
    brand: Mapped[str] = mapped_column(String(50), nullable=True, comment="品牌")
    spec: Mapped[str] = mapped_column(String(50), nullable=True, comment="规格")
    
    # 价格和成本
    sale_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, comment="销售价格")
    cost_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, comment="成本价格")
    
    # 状态
    status: Mapped[str] = mapped_column(String(20), default="active", comment="状态: active-在售, inactive-下架")
    description: Mapped[str] = mapped_column(Text, nullable=True, comment="商品描述")
    
    # 时间字段
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    
    # 关系
    order_items: Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="product")
    inventories: Mapped[list["Inventory"]] = relationship("Inventory", back_populates="product")
    
    @property
    def profit_margin(self) -> Decimal:
        """
        计算毛利率
        毛利率 = (售价 - 成本) / 售价 * 100%
        """
        if self.sale_price == 0:
            return Decimal(0)
        return (self.sale_price - self.cost_price) / self.sale_price * 100
    
    def __repr__(self):
        return f"<Product {self.product_code} - {self.product_name}>"


class User(Base):
    """
    用户表 - 存储购买用户信息
    """
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="用户ID")
    user_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="用户编号")
    phone: Mapped[str] = mapped_column(String(20), nullable=True, unique=True, comment="手机号")
    nickname: Mapped[str] = mapped_column(String(50), nullable=True, comment="昵称")
    
    # 用户类型
    user_type: Mapped[str] = mapped_column(String(20), default="normal", comment="用户类型: normal-普通用户, member-会员")
    
    # 统计信息
    total_orders: Mapped[int] = mapped_column(Integer, default=0, comment="总订单数")
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, comment="总消费金额")
    
    # 时间字段
    register_date: Mapped[date] = mapped_column(Date, default=date.today, comment="注册日期")
    last_purchase_time: Mapped[datetime] = mapped_column(DateTime, nullable=True, comment="最后购买时间")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    
    # 关系
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="user")
    
    def __repr__(self):
        return f"<User {self.user_code} - {self.nickname or self.phone}>"


class Order(Base):
    """
    订单表 - 存储订单主信息
    """
    __tablename__ = "orders"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="订单ID")
    order_no: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, comment="订单编号")
    
    # 外键关联
    device_id: Mapped[int] = mapped_column(Integer, ForeignKey("devices.id"), nullable=False, comment="设备ID")
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, comment="用户ID(可为空，匿名购买)")
    
    # 订单金额
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, comment="订单总金额")
    total_quantity: Mapped[int] = mapped_column(Integer, default=1, comment="商品总数")
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, comment="优惠金额")
    pay_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, comment="实付金额")
    
    # 支付信息
    pay_method: Mapped[str] = mapped_column(String(20), default="wechat", comment="支付方式: wechat-微信, alipay-支付宝, cash-现金")
    pay_status: Mapped[str] = mapped_column(String(20), default="success", comment="支付状态: pending-待支付, success-成功, failed-失败, refund-退款")
    
    # 时间字段
    order_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True, comment="下单时间")
    pay_time: Mapped[datetime] = mapped_column(DateTime, nullable=True, comment="支付时间")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="创建时间")
    
    # 关系
    device: Mapped["Device"] = relationship("Device", back_populates="orders")
    user: Mapped["User"] = relationship("User", back_populates="orders")
    order_items: Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Order {self.order_no} - {self.pay_amount}>"


class OrderItem(Base):
    """
    订单明细表 - 存储订单中的商品明细
    """
    __tablename__ = "order_items"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="明细ID")
    
    # 外键关联
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id"), nullable=False, comment="订单ID")
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False, comment="商品ID")
    
    # 商品信息
    product_name: Mapped[str] = mapped_column(String(100), nullable=False, comment="商品名称(冗余)")
    product_code: Mapped[str] = mapped_column(String(50), nullable=False, comment="商品编码(冗余)")
    
    # 数量和金额
    quantity: Mapped[int] = mapped_column(Integer, default=1, comment="购买数量")
    sale_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, comment="销售单价")
    cost_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, comment="成本单价")
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, comment="小计金额")
    
    # 时间字段
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="创建时间")
    
    # 关系
    order: Mapped["Order"] = relationship("Order", back_populates="order_items")
    product: Mapped["Product"] = relationship("Product", back_populates="order_items")
    
    @property
    def profit(self) -> Decimal:
        """
        计算该明细的利润
        """
        return (self.sale_price - self.cost_price) * self.quantity
    
    def __repr__(self):
        return f"<OrderItem {self.product_name} x {self.quantity}>"


class Inventory(Base):
    """
    库存表 - 存储设备中商品的库存信息
    """
    __tablename__ = "inventories"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="库存ID")
    
    # 外键关联
    device_id: Mapped[int] = mapped_column(Integer, ForeignKey("devices.id"), nullable=False, comment="设备ID")
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False, comment="商品ID")
    
    # 库存信息
    slot_number: Mapped[str] = mapped_column(String(20), nullable=True, comment="货道编号")
    current_quantity: Mapped[int] = mapped_column(Integer, default=0, comment="当前库存")
    max_quantity: Mapped[int] = mapped_column(Integer, default=0, comment="最大库存")
    min_quantity: Mapped[int] = mapped_column(Integer, default=5, comment="最低库存预警线")
    
    # 时间字段
    last_restock_time: Mapped[datetime] = mapped_column(DateTime, nullable=True, comment="上次补货时间")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    
    # 关系
    device: Mapped["Device"] = relationship("Device", back_populates="inventories")
    product: Mapped["Product"] = relationship("Product", back_populates="inventories")
    
    @property
    def available_quantity(self) -> int:
        """
        可补货数量
        """
        return self.max_quantity - self.current_quantity
    
    @property
    def is_low_stock(self) -> bool:
        """
        是否库存不足
        """
        return self.current_quantity <= self.min_quantity
    
    def __repr__(self):
        return f"<Inventory 设备{self.device_id} 商品{self.product_id}: {self.current_quantity}>"


class Maintenance(Base):
    """
    运维记录表 - 存储设备维护和故障记录
    """
    __tablename__ = "maintenances"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="运维记录ID")
    
    # 外键关联
    device_id: Mapped[int] = mapped_column(Integer, ForeignKey("devices.id"), nullable=False, comment="设备ID")
    
    # 运维类型
    maintenance_type: Mapped[str] = mapped_column(String(20), nullable=False, comment="类型: fault-故障, routine-例行维护, repair-维修, upgrade-升级")
    
    # 故障/维护信息
    title: Mapped[str] = mapped_column(String(200), nullable=False, comment="标题")
    description: Mapped[str] = mapped_column(Text, nullable=True, comment="详细描述")
    solution: Mapped[str] = mapped_column(Text, nullable=True, comment="解决方案")
    
    # 成本信息
    cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, comment="运维成本(元)")
    duration_minutes: Mapped[int] = mapped_column(Integer, default=0, comment="处理时长(分钟)")
    
    # 状态
    status: Mapped[str] = mapped_column(String(20), default="pending", comment="状态: pending-待处理, processing-处理中, completed-已完成, cancelled-已取消")
    
    # 时间字段
    report_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="上报时间")
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=True, comment="开始处理时间")
    complete_time: Mapped[datetime] = mapped_column(DateTime, nullable=True, comment="完成时间")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    
    # 关系
    device: Mapped["Device"] = relationship("Device", back_populates="maintenances")
    
    def __repr__(self):
        return f"<Maintenance {self.id} - {self.title}>"
