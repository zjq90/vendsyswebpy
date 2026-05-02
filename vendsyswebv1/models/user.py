"""
用户模型
定义系统用户（管理员、业务员）的数据结构
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from database import Base


class User(Base):
    """
    用户表模型
    存储系统用户信息，包括管理员和业务员
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False, comment="用户名")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    real_name = Column(String(50), nullable=False, comment="真实姓名")
    role = Column(String(20), nullable=False, default="salesman", comment="角色: admin(管理员), salesman(业务员)")
    email = Column(String(100), nullable=True, comment="邮箱")
    phone = Column(String(20), nullable=True, comment="电话")
    is_active = Column(Boolean, default=True, comment="是否激活")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"
