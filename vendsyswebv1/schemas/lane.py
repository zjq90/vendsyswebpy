"""
货道相关的Pydantic模型
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class LaneBase(BaseModel):
    """货道基础模型"""
    lane_number: int = Field(..., description="货道编号")
    lane_code: Optional[str] = Field(None, max_length=50, description="货道代码")
    lane_name: Optional[str] = Field(None, max_length=100, description="货道名称")
    row: Optional[int] = Field(None, description="行号")
    col: Optional[int] = Field(None, description="列号")
    total_capacity: int = Field(default=10, gt=0, description="总容量")
    current_stock: int = Field(default=0, ge=0, description="当前库存")
    min_stock_threshold: int = Field(default=2, ge=0, description="最低库存预警")
    sale_price: Optional[float] = Field(None, gt=0, description="售价")
    status: Optional[str] = Field(default="normal", max_length=20, description="状态")
    motor_status: Optional[str] = Field(default="normal", max_length=20, description="电机状态")
    sensor_status: Optional[str] = Field(default="normal", max_length=20, description="传感器状态")
    motor_type: Optional[str] = Field(None, max_length=50, description="电机类型")
    motor_power: Optional[int] = Field(None, description="电机功率")
    rotation_degrees: Optional[int] = Field(None, description="旋转角度")


class LaneCreate(LaneBase):
    """创建货道请求模型"""
    device_id: int = Field(..., description="设备ID")
    product_id: Optional[int] = Field(None, description="商品ID")


class LaneUpdate(BaseModel):
    """更新货道请求模型"""
    product_id: Optional[int] = Field(None)
    lane_name: Optional[str] = Field(None, max_length=100)
    row: Optional[int] = Field(None)
    col: Optional[int] = Field(None)
    total_capacity: Optional[int] = Field(None, gt=0)
    current_stock: Optional[int] = Field(None, ge=0)
    min_stock_threshold: Optional[int] = Field(None, ge=0)
    sale_price: Optional[float] = Field(None, gt=0)
    status: Optional[str] = Field(None, max_length=20)
    motor_status: Optional[str] = Field(None, max_length=20)
    sensor_status: Optional[str] = Field(None, max_length=20)


class LaneProductResponse(BaseModel):
    """货道商品信息响应"""
    id: int
    product_code: str
    product_name: str
    price: float
    product_type: Optional[str]
    brand: Optional[str]

    class Config:
        from_attributes = True


class LaneResponse(LaneBase):
    """货道响应模型"""
    id: int
    device_id: int
    product_id: Optional[int]
    product: Optional[LaneProductResponse]
    total_sales: int
    today_sales: int
    last_sale_time: Optional[datetime]
    last_refill_time: Optional[datetime]
    last_refill_quantity: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
