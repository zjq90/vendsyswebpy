"""
商品模型
定义设备内商品的基本信息
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text
from database import Base


class Product(Base):
    """
    商品表模型
    存储商品的基本信息，可在多个设备中使用
    """
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_code = Column(String(50), unique=True, index=True, nullable=False, comment="商品编码")
    product_name = Column(String(200), nullable=False, comment="商品名称")
    product_type = Column(String(50), nullable=True, comment="商品类型: 饮料, 零食, 日用品等")
    brand = Column(String(100), nullable=True, comment="品牌")
    specification = Column(String(100), nullable=True, comment="规格型号")
    unit = Column(String(20), default="件", comment="单位")

    # 价格信息
    price = Column(Float, nullable=False, comment="售价")
    cost_price = Column(Float, nullable=True, comment="成本价")
    original_price = Column(Float, nullable=True, comment="原价")

    # 分类信息
    category = Column(String(50), nullable=True, comment="分类")
    sub_category = Column(String(50), nullable=True, comment="子分类")

    # 描述信息
    description = Column(Text, nullable=True, comment="商品描述")
    image_url = Column(String(500), nullable=True, comment="商品图片URL")

    # 保质期信息
    shelf_life_days = Column(Integer, nullable=True, comment="保质期(天)")
    storage_condition = Column(String(200), nullable=True, comment="存储条件")

    # 状态信息
    is_active = Column(Boolean, default=True, comment="是否启用")
    sort_order = Column(Integer, default=0, comment="排序号")

    # 时间信息
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    def __repr__(self):
        return f"<Product(id={self.id}, product_code={self.product_code}, product_name={self.product_name})>"
