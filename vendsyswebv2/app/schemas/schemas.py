from datetime import datetime, time
from typing import Optional, List
from pydantic import BaseModel, Field


class CategoryBase(BaseModel):
    """分类基础模型"""
    name: str = Field(..., min_length=1, max_length=100, description="分类名称")
    description: Optional[str] = Field(None, max_length=500, description="分类描述")


class CategoryCreate(CategoryBase):
    """创建分类模型"""
    pass


class CategoryUpdate(CategoryBase):
    """更新分类模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)


class CategoryResponse(CategoryBase):
    """分类响应模型"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    """商品基础模型"""
    name: str = Field(..., min_length=1, max_length=200, description="商品名称")
    image_url: Optional[str] = Field(None, max_length=500, description="商品图片URL")
    specification: Optional[str] = Field(None, max_length=100, description="商品规格")
    barcode: Optional[str] = Field(None, max_length=50, description="条形码")
    category_id: int = Field(..., description="分类ID")
    cost_price: float = Field(..., gt=0, description="成本价")
    retail_price: float = Field(..., gt=0, description="零售价")
    description: Optional[str] = Field(None, description="商品描述")
    status: str = Field(default="active", description="状态")


class ProductCreate(ProductBase):
    """创建商品模型"""
    pass


class ProductUpdate(BaseModel):
    """更新商品模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    image_url: Optional[str] = Field(None, max_length=500)
    specification: Optional[str] = Field(None, max_length=100)
    barcode: Optional[str] = Field(None, max_length=50)
    category_id: Optional[int] = None
    cost_price: Optional[float] = Field(None, gt=0)
    retail_price: Optional[float] = Field(None, gt=0)
    description: Optional[str] = None
    status: Optional[str] = None


class ProductResponse(ProductBase):
    """商品响应模型"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    category: Optional[CategoryResponse] = None
    
    class Config:
        from_attributes = True


class VendingMachineBase(BaseModel):
    """售货机基础模型"""
    name: str = Field(..., min_length=1, max_length=100, description="售货机名称")
    serial_number: str = Field(..., min_length=1, max_length=50, description="设备序列号")
    location: Optional[str] = Field(None, max_length=200, description="安装位置")
    region: Optional[str] = Field(None, max_length=50, description="区域标识")
    status: str = Field(default="offline", description="设备状态")
    row_count: int = Field(default=6, ge=1, description="货道行数")
    column_count: int = Field(default=8, ge=1, description="货道列数")
    description: Optional[str] = Field(None, description="设备描述")


class VendingMachineCreate(VendingMachineBase):
    """创建售货机模型"""
    pass


class VendingMachineUpdate(BaseModel):
    """更新售货机模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    serial_number: Optional[str] = Field(None, min_length=1, max_length=50)
    location: Optional[str] = Field(None, max_length=200)
    region: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = None
    row_count: Optional[int] = Field(None, ge=1)
    column_count: Optional[int] = Field(None, ge=1)
    description: Optional[str] = None


class VendingMachineResponse(VendingMachineBase):
    """售货机响应模型"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AisleBase(BaseModel):
    """货道基础模型"""
    vending_machine_id: int = Field(..., description="售货机ID")
    aisle_code: str = Field(..., min_length=1, max_length=10, description="货道编号")
    row_number: int = Field(..., ge=1, description="行号")
    column_number: int = Field(..., ge=1, description="列号")
    max_capacity: int = Field(default=10, ge=1, description="最大容量")
    status: str = Field(default="empty", description="货道状态")


class AisleCreate(AisleBase):
    """创建货道模型"""
    pass


class AisleUpdate(BaseModel):
    """更新货道模型"""
    max_capacity: Optional[int] = Field(None, ge=1)
    status: Optional[str] = None


class AisleResponse(AisleBase):
    """货道响应模型"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AisleProductBase(BaseModel):
    """货道商品绑定基础模型"""
    aisle_id: int = Field(..., description="货道ID")
    product_id: int = Field(..., description="商品ID")
    current_stock: int = Field(default=0, ge=0, description="当前库存量")
    stock_threshold: int = Field(default=5, ge=0, description="库存阈值")
    sale_price: Optional[float] = Field(None, gt=0, description="销售价格")
    status: str = Field(default="active", description="绑定状态")


class AisleProductCreate(AisleProductBase):
    """创建货道商品绑定模型"""
    pass


class AisleProductUpdate(BaseModel):
    """更新货道商品绑定模型"""
    product_id: Optional[int] = None
    current_stock: Optional[int] = Field(None, ge=0)
    stock_threshold: Optional[int] = Field(None, ge=0)
    sale_price: Optional[float] = Field(None, gt=0)
    status: Optional[str] = None


class BatchAisleProductCreate(BaseModel):
    """批量创建货道商品绑定模型"""
    vending_machine_id: int = Field(..., description="售货机ID")
    bindings: List[AisleProductCreate] = Field(..., description="绑定列表")


class AisleProductResponse(AisleProductBase):
    """货道商品绑定响应模型"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    product: Optional[ProductResponse] = None
    aisle: Optional[AisleResponse] = None
    
    class Config:
        from_attributes = True


class InventoryRecordBase(BaseModel):
    """库存记录基础模型"""
    aisle_product_id: int = Field(..., description="货道商品绑定ID")
    change_type: str = Field(..., description="变更类型")
    change_quantity: int = Field(..., description="变更数量")
    before_stock: int = Field(..., description="变更前库存")
    after_stock: int = Field(..., description="变更后库存")
    order_number: Optional[str] = Field(None, max_length=50, description="关联订单号")
    operator_id: Optional[int] = Field(None, description="操作人ID")
    remark: Optional[str] = Field(None, description="备注")


class InventoryRecordResponse(InventoryRecordBase):
    """库存记录响应模型"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class ReplenishmentOrderBase(BaseModel):
    """补货单基础模型"""
    order_number: Optional[str] = Field(None, max_length=50, description="补货单号")
    vending_machine_id: int = Field(..., description="售货机ID")
    aisle_product_id: int = Field(..., description="货道商品绑定ID")
    current_stock: int = Field(..., description="当前库存")
    stock_threshold: int = Field(..., description="库存阈值")
    suggested_quantity: int = Field(default=10, description="建议补货数量")
    actual_quantity: Optional[int] = Field(None, description="实际补货数量")
    status: str = Field(default="pending", description="状态")
    priority: str = Field(default="medium", description="优先级")
    assignee_id: Optional[int] = Field(None, description="负责人ID")
    remark: Optional[str] = Field(None, description="备注")


class ReplenishmentOrderCreate(ReplenishmentOrderBase):
    """创建补货单模型"""
    pass


class ReplenishmentOrderUpdate(BaseModel):
    """更新补货单模型"""
    actual_quantity: Optional[int] = Field(None, ge=0)
    status: Optional[str] = None
    priority: Optional[str] = None
    assignee_id: Optional[int] = None
    remark: Optional[str] = None


class ReplenishmentOrderResponse(ReplenishmentOrderBase):
    """补货单响应模型"""
    id: int
    reminder_sent: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PriceStrategyBase(BaseModel):
    """价格策略基础模型"""
    name: str = Field(..., min_length=1, max_length=100, description="策略名称")
    strategy_type: str = Field(..., description="策略类型")
    product_id: Optional[int] = Field(None, description="商品ID")
    start_time: Optional[time] = Field(None, description="开始时间")
    end_time: Optional[time] = Field(None, description="结束时间")
    applicable_days: Optional[str] = Field(None, max_length=20, description="适用星期")
    applicable_region: Optional[str] = Field(None, max_length=50, description="适用区域")
    discount_type: str = Field(default="percentage", description="折扣类型")
    discount_value: float = Field(..., description="折扣值")
    priority: int = Field(default=1, description="优先级")
    status: str = Field(default="active", description="状态")
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")
    description: Optional[str] = Field(None, description="策略描述")


class PriceStrategyCreate(PriceStrategyBase):
    """创建价格策略模型"""
    pass


class PriceStrategyUpdate(BaseModel):
    """更新价格策略模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    strategy_type: Optional[str] = None
    product_id: Optional[int] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    applicable_days: Optional[str] = None
    applicable_region: Optional[str] = None
    discount_type: Optional[str] = None
    discount_value: Optional[float] = None
    priority: Optional[int] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    description: Optional[str] = None


class PriceStrategyResponse(PriceStrategyBase):
    """价格策略响应模型"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class SalesCreate(BaseModel):
    """销售创建模型"""
    aisle_product_id: int = Field(..., description="货道商品绑定ID")
    quantity: int = Field(default=1, ge=1, description="销售数量")
    order_number: Optional[str] = Field(None, max_length=50, description="订单号")


class ApiResponse(BaseModel):
    """通用API响应模型"""
    success: bool = True
    message: str = "操作成功"
    data: Optional[dict] = None
