from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Category(Base):
    """
    商品分类模型
    用于管理商品的分类信息
    """
    __tablename__ = "categories"
    
    # 主键ID
    id = Column(Integer, primary_key=True, index=True, comment="分类ID")
    
    # 分类名称
    name = Column(String(100), unique=True, nullable=False, index=True, comment="分类名称")
    
    # 分类描述
    description = Column(String(500), comment="分类描述")
    
    # 创建时间和更新时间
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关系：一个分类可以有多个商品
    products = relationship("Product", back_populates="category", cascade="all, delete-orphan")
    
    def __repr__(self):
        """字符串表示"""
        return f"<Category(id={self.id}, name='{self.name}')>"
