"""
自动售后机数据统计与分析系统 - Pydantic模型
用于API请求和响应的数据验证
"""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field


# ==================== 基础模型 ====================

class DeviceBase(BaseModel):
    device_code: str = Field(..., description="设备编号", max_length=50)
    device_name: str = Field(..., description="设备名称", max_length=100)
    location: str = Field(..., description="设备位置", max_length=200)
    status: Optional[str] = Field(default="normal", description="设备状态")
    capacity: Optional[int] = Field(default=0, description="总容量")
    slot_count: Optional[int] = Field(default=0, description="货道数量")
    install_date: Optional[date] = Field(None, description="安装日期")


class DeviceCreate(DeviceBase):
    pass


class DeviceUpdate(BaseModel):
    device_name: Optional[str] = Field(None, description="设备名称")
    location: Optional[str] = Field(None, description="设备位置")
    status: Optional[str] = Field(None, description="设备状态")
    capacity: Optional[int] = Field(None, description="总容量")
    slot_count: Optional[int] = Field(None, description="货道数量")


class DeviceResponse(DeviceBase):
    id: int = Field(..., description="设备ID")
    last_maintenance_date: Optional[date] = Field(None, description="上次维护日期")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    product_code: str = Field(..., description="商品编码", max_length=50)
    product_name: str = Field(..., description="商品名称", max_length=100)
    category: Optional[str] = Field(None, description="商品分类", max_length=50)
    brand: Optional[str] = Field(None, description="品牌", max_length=50)
    spec: Optional[str] = Field(None, description="规格", max_length=50)
    sale_price: Decimal = Field(..., description="销售价格", gt=0)
    cost_price: Decimal = Field(..., description="成本价格", gt=0)
    status: Optional[str] = Field(default="active", description="状态")
    description: Optional[str] = Field(None, description="商品描述")


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    product_name: Optional[str] = Field(None, description="商品名称")
    category: Optional[str] = Field(None, description="商品分类")
    brand: Optional[str] = Field(None, description="品牌")
    spec: Optional[str] = Field(None, description="规格")
    sale_price: Optional[Decimal] = Field(None, description="销售价格")
    cost_price: Optional[Decimal] = Field(None, description="成本价格")
    status: Optional[str] = Field(None, description="状态")
    description: Optional[str] = Field(None, description="商品描述")


class ProductResponse(ProductBase):
    id: int = Field(..., description="商品ID")
    profit_margin: Optional[float] = Field(None, description="毛利率")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class UserBase(BaseModel):
    user_code: str = Field(..., description="用户编号", max_length=50)
    phone: Optional[str] = Field(None, description="手机号", max_length=20)
    nickname: Optional[str] = Field(None, description="昵称", max_length=50)
    user_type: Optional[str] = Field(default="normal", description="用户类型")


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    phone: Optional[str] = Field(None, description="手机号")
    nickname: Optional[str] = Field(None, description="昵称")
    user_type: Optional[str] = Field(None, description="用户类型")


class UserResponse(UserBase):
    id: int = Field(..., description="用户ID")
    total_orders: int = Field(default=0, description="总订单数")
    total_amount: Decimal = Field(default=0, description="总消费金额")
    register_date: date = Field(..., description="注册日期")
    last_purchase_time: Optional[datetime] = Field(None, description="最后购买时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class OrderItemBase(BaseModel):
    product_id: int = Field(..., description="商品ID")
    quantity: int = Field(default=1, description="购买数量", gt=0)


class OrderItemResponse(BaseModel):
    id: int = Field(..., description="明细ID")
    order_id: int = Field(..., description="订单ID")
    product_id: int = Field(..., description="商品ID")
    product_name: str = Field(..., description="商品名称")
    product_code: str = Field(..., description="商品编码")
    quantity: int = Field(..., description="购买数量")
    sale_price: Decimal = Field(..., description="销售单价")
    cost_price: Decimal = Field(..., description="成本单价")
    subtotal: Decimal = Field(..., description="小计金额")
    profit: Optional[float] = Field(None, description="利润")
    created_at: datetime = Field(..., description="创建时间")
    
    class Config:
        from_attributes = True


class OrderBase(BaseModel):
    device_id: int = Field(..., description="设备ID")
    user_id: Optional[int] = Field(None, description="用户ID")
    pay_method: Optional[str] = Field(default="wechat", description="支付方式")
    items: List[OrderItemBase] = Field(..., description="订单商品列表")


class OrderCreate(OrderBase):
    pass


class OrderResponse(BaseModel):
    id: int = Field(..., description="订单ID")
    order_no: str = Field(..., description="订单编号")
    device_id: int = Field(..., description="设备ID")
    user_id: Optional[int] = Field(None, description="用户ID")
    total_amount: Decimal = Field(..., description="订单总金额")
    total_quantity: int = Field(..., description="商品总数")
    discount_amount: Decimal = Field(default=0, description="优惠金额")
    pay_amount: Decimal = Field(..., description="实付金额")
    pay_method: str = Field(..., description="支付方式")
    pay_status: str = Field(..., description="支付状态")
    order_time: datetime = Field(..., description="下单时间")
    pay_time: Optional[datetime] = Field(None, description="支付时间")
    created_at: datetime = Field(..., description="创建时间")
    order_items: List[OrderItemResponse] = Field(default=[], description="订单明细")
    
    class Config:
        from_attributes = True


# ==================== 统计分析模型 ====================

class SalesSummary(BaseModel):
    """销售汇总统计"""
    total_amount: Decimal = Field(default=0, description="总销售额")
    total_orders: int = Field(default=0, description="总订单数")
    total_quantity: int = Field(default=0, description="总商品数")
    avg_order_value: float = Field(default=0, description="客单价")
    period: str = Field(..., description="统计周期")


class DailySalesData(BaseModel):
    """日销售数据"""
    date: str = Field(..., description="日期")
    amount: float = Field(default=0, description="销售额")
    orders: int = Field(default=0, description="订单数")
    quantity: int = Field(default=0, description="商品数")


class WeeklySalesData(BaseModel):
    """周销售数据"""
    week: str = Field(..., description="周")
    amount: float = Field(default=0, description="销售额")
    orders: int = Field(default=0, description="订单数")


class MonthlySalesData(BaseModel):
    """月销售数据"""
    month: str = Field(..., description="月份")
    amount: float = Field(default=0, description="销售额")
    orders: int = Field(default=0, description="订单数")


class YearlySalesData(BaseModel):
    """年销售数据"""
    year: str = Field(..., description="年份")
    amount: float = Field(default=0, description="销售额")
    orders: int = Field(default=0, description="订单数")


class HotProductItem(BaseModel):
    """热销商品"""
    id: int = Field(..., description="商品ID")
    product_name: str = Field(..., description="商品名称")
    category: Optional[str] = Field(None, description="分类")
    total_quantity: int = Field(default=0, description="销售数量")
    total_amount: float = Field(default=0, description="销售金额")
    profit_margin: float = Field(default=0, description="毛利率")


class SlowSellingItem(BaseModel):
    """滞销商品"""
    id: int = Field(..., description="商品ID")
    product_name: str = Field(..., description="商品名称")
    category: Optional[str] = Field(None, description="分类")
    total_quantity: int = Field(default=0, description="销售数量")
    total_amount: float = Field(default=0, description="销售金额")
    last_sale_days: int = Field(default=0, description="距上次销售天数")


class ProfitMarginAnalysis(BaseModel):
    """毛利率分析"""
    category: str = Field(..., description="分类")
    total_amount: float = Field(default=0, description="销售金额")
    total_cost: float = Field(default=0, description="成本金额")
    profit: float = Field(default=0, description="利润")
    profit_margin: float = Field(default=0, description="毛利率")


class DevicePerformance(BaseModel):
    """设备效能分析"""
    id: int = Field(..., description="设备ID")
    device_code: str = Field(..., description="设备编号")
    device_name: str = Field(..., description="设备名称")
    location: str = Field(..., description="位置")
    status: str = Field(..., description="状态")
    total_amount: float = Field(default=0, description="总销售额")
    total_orders: int = Field(default=0, description="总订单数")
    avg_daily_amount: float = Field(default=0, description="日均销售额")
    fault_count: int = Field(default=0, description="故障次数")
    maintenance_cost: float = Field(default=0, description="运维成本")


class UserBehaviorAnalysis(BaseModel):
    """用户行为分析"""
    period: str = Field(..., description="统计周期")
    total_users: int = Field(default=0, description="总用户数")
    active_users: int = Field(default=0, description="活跃用户数")
    new_users: int = Field(default=0, description="新用户数")
    repeat_purchase_users: int = Field(default=0, description="复购用户数")
    repeat_purchase_rate: float = Field(default=0, description="复购率")
    avg_purchase_count: float = Field(default=0, description="平均购买次数")
    avg_order_value: float = Field(default=0, description="客单价")


class TimeSlotData(BaseModel):
    """购买时段数据"""
    hour: int = Field(..., description="小时")
    order_count: int = Field(default=0, description="订单数")
    amount: float = Field(default=0, description="销售额")


class DashboardOverview(BaseModel):
    """可视化大屏概览"""
    today_amount: float = Field(default=0, description="今日销售额")
    today_orders: int = Field(default=0, description="今日订单数")
    total_devices: int = Field(default=0, description="设备总数")
    online_devices: int = Field(default=0, description="在线设备数")
    total_users: int = Field(default=0, description="总用户数")
    today_new_users: int = Field(default=0, description="今日新用户")
    month_amount: float = Field(default=0, description="本月销售额")
    month_orders: int = Field(default=0, description="本月订单数")
    year_amount: float = Field(default=0, description="本年销售额")


# ==================== 通用响应模型 ====================

class ApiResponse(BaseModel):
    """通用API响应"""
    code: int = Field(default=200, description="状态码")
    message: str = Field(default="success", description="消息")
    data: Optional[dict] = Field(None, description="数据")


class PaginatedResponse(BaseModel):
    """分页响应"""
    code: int = Field(default=200, description="状态码")
    message: str = Field(default="success", description="消息")
    data: List = Field(default=[], description="数据列表")
    total: int = Field(default=0, description="总记录数")
    page: int = Field(default=1, description="当前页")
    page_size: int = Field(default=10, description="每页大小")
    total_pages: int = Field(default=0, description="总页数")
