"""
商品相关的Pydantic模型
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ProductBase(BaseModel):
    """商品基础模型"""
    product_code: str = Field(..., max_length=50, description="商品编码")
    product_name: str = Field(..., max_length=200, description="商品名称")
    product_type: Optional[str] = Field(None, max_length=50, description="商品类型")
    brand: Optional[str] = Field(None, max_length=100, description="品牌")
    specification: Optional[str] = Field(None, max_length=100, description="规格型号")
    unit: Optional[str] = Field(default="件", max_length=20, description="单位")
    price: float = Field(..., gt=0, description="售价")
    cost_price: Optional[float] = Field(None, gt=0, description="成本价")
    original_price: Optional[float] = Field(None, gt=0, description="原价")
    category: Optional[str] = Field(None, max_length=50, description="分类")
    sub_category: Optional[str] = Field(None, max_length=50, description="子分类")
    description: Optional[str] = Field(None, description="商品描述")
    image_url: Optional[str] = Field(None, max_length=500, description="图片URL")
    shelf_life_days: Optional[int] = Field(None, description="保质期(天)")
    storage_condition: Optional[str] = Field(None, max_length=200, description="存储条件")
    is_active: Optional[bool] = Field(default=True, description="是否启用")
    sort_order: Optional[int] = Field(default=0, description="排序号")


class ProductCreate(ProductBase):
    """创建商品请求模型"""
    pass


class ProductUpdate(BaseModel):
    """更新商品请求模型"""
    product_name: Optional[str] = Field(None, max_length=200)
    product_type: Optional[str] = Field(None, max_length=50)
    brand: Optional[str] = Field(None, max_length=100)
    specification: Optional[str] = Field(None, max_length=100)
    price: Optional[float] = Field(None, gt=0)
    cost_price: Optional[float] = Field(None, gt=0)
    original_price: Optional[float] = Field(None, gt=0)
    category: Optional[str] = Field(None, max_length=50)
    sub_category: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None)
    image_url: Optional[str] = Field(None, max_length=500)
    shelf_life_days: Optional[int] = Field(None)
    storage_condition: Optional[str] = Field(None, max_length=200)
    is_active: Optional[bool] = Field(None)
    sort_order: Optional[int] = Field(None)


class ProductResponse(ProductBase):
    """商品响应模型"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
