import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# 获取当前目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'vending_system.db')}"

# 创建数据库引擎
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# 创建会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 声明基类
Base = declarative_base()

# ==================== 数据库模型 ====================

class Role(Base):
    """角色表"""
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False, comment="角色名称")
    code = Column(String(50), unique=True, nullable=False, comment="角色编码")
    description = Column(String(200), comment="角色描述")
    is_system = Column(Boolean, default=False, comment="是否系统内置角色")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联
    users = relationship("User", back_populates="role_obj")
    role_permissions = relationship("RolePermission", back_populates="role")


class Permission(Base):
    """权限表（菜单和操作权限）"""
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="权限名称")
    code = Column(String(100), unique=True, nullable=False, comment="权限编码")
    type = Column(String(20), nullable=False, comment="权限类型: menu-菜单, button-按钮")
    parent_id = Column(Integer, ForeignKey("permissions.id"), nullable=True, comment="父级权限ID")
    path = Column(String(200), comment="前端路由路径")
    icon = Column(String(50), comment="图标")
    sort_order = Column(Integer, default=0, comment="排序")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 自关联
    children = relationship("Permission", backref="parent", remote_side=[id])
    role_permissions = relationship("RolePermission", back_populates="permission")


class RolePermission(Base):
    """角色权限关联表"""
    __tablename__ = "role_permissions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    permission_id = Column(Integer, ForeignKey("permissions.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    
    # 关联
    role = relationship("Role", back_populates="role_permissions")
    permission = relationship("Permission", back_populates="role_permissions")


class Franchisee(Base):
    """加盟商/代理商表 - 支持多级结构"""
    __tablename__ = "franchisees"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="加盟商名称")
    code = Column(String(50), unique=True, nullable=False, comment="加盟商编码")
    type = Column(String(20), nullable=False, comment="类型: agent-代理商, franchisee-加盟商")
    level = Column(Integer, default=1, comment="层级: 1-一级, 2-二级, 3-三级")
    parent_id = Column(Integer, ForeignKey("franchisees.id"), nullable=True, comment="上级加盟商ID")
    contact_person = Column(String(50), comment="联系人")
    contact_phone = Column(String(20), comment="联系电话")
    contact_email = Column(String(100), comment="联系邮箱")
    address = Column(String(200), comment="地址")
    description = Column(Text, comment="描述")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 自关联
    children = relationship("Franchisee", backref="parent", remote_side=[id])
    users = relationship("User", back_populates="franchisee")
    devices = relationship("Device", back_populates="franchisee")


class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, comment="用户名")
    password = Column(String(255), nullable=False, comment="密码(加密)")
    real_name = Column(String(50), comment="真实姓名")
    phone = Column(String(20), comment="手机号")
    email = Column(String(100), comment="邮箱")
    avatar = Column(String(255), comment="头像")
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=True, comment="角色ID")
    franchisee_id = Column(Integer, ForeignKey("franchisees.id"), nullable=True, comment="加盟商ID")
    is_superuser = Column(Boolean, default=False, comment="是否超级管理员")
    is_active = Column(Boolean, default=True, comment="是否启用")
    last_login_at = Column(DateTime, nullable=True, comment="最后登录时间")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联
    role_obj = relationship("Role", back_populates="users")
    franchisee = relationship("Franchisee", back_populates="users")
    logs = relationship("OperationLog", back_populates="user")


class OperationLog(Base):
    """操作日志表"""
    __tablename__ = "operation_logs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="操作用户ID")
    username = Column(String(50), comment="操作用户名")
    module = Column(String(50), comment="操作模块")
    action = Column(String(50), comment="操作类型")
    description = Column(String(500), comment="操作描述")
    request_method = Column(String(10), comment="请求方法")
    request_path = Column(String(200), comment="请求路径")
    request_params = Column(Text, comment="请求参数(JSON)")
    response_code = Column(Integer, comment="响应状态码")
    ip_address = Column(String(50), comment="IP地址")
    user_agent = Column(String(255), comment="用户代理")
    execute_time = Column(Integer, comment="执行时间(ms)")
    created_at = Column(DateTime, default=datetime.now)
    
    # 关联
    user = relationship("User", back_populates="logs")


class SystemConfig(Base):
    """系统配置表"""
    __tablename__ = "system_configs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    category = Column(String(50), nullable=False, comment="配置分类")
    key = Column(String(100), unique=True, nullable=False, comment="配置键")
    value = Column(Text, comment="配置值")
    description = Column(String(200), comment="配置描述")
    is_public = Column(Boolean, default=False, comment="是否公开配置")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class Device(Base):
    """设备表 - 用于关联加盟商和数据展示"""
    __tablename__ = "devices"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_no = Column(String(50), unique=True, nullable=False, comment="设备编号")
    name = Column(String(100), comment="设备名称")
    model = Column(String(50), comment="设备型号")
    franchisee_id = Column(Integer, ForeignKey("franchisees.id"), nullable=True, comment="所属加盟商ID")
    location = Column(String(200), comment="放置位置")
    status = Column(String(20), default="offline", comment="状态: online-在线, offline-离线, fault-故障")
    last_online_at = Column(DateTime, nullable=True, comment="最后在线时间")
    description = Column(Text, comment="描述")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联
    franchisee = relationship("Franchisee", back_populates="devices")
    transactions = relationship("Transaction", back_populates="device")


class Transaction(Base):
    """交易记录表 - 用于可视化大屏"""
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_no = Column(String(50), unique=True, nullable=False, comment="订单号")
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=True, comment="设备ID")
    total_amount = Column(Numeric(10, 2), default=0, comment="订单金额")
    pay_amount = Column(Numeric(10, 2), default=0, comment="实付金额")
    pay_type = Column(String(20), comment="支付方式: wechat-微信, alipay-支付宝, cash-现金")
    status = Column(String(20), default="pending", comment="状态: pending-待支付, success-成功, failed-失败, refunded-已退款")
    pay_time = Column(DateTime, nullable=True, comment="支付时间")
    created_at = Column(DateTime, default=datetime.now)
    
    # 关联
    device = relationship("Device", back_populates="transactions")


# ==================== 数据库操作函数 ====================

def init_db():
    """初始化数据库表"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
