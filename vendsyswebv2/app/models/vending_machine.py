from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


class VendingMachine(Base):
    """
    售货机模型
    管理售货机设备信息
    """
    __tablename__ = "vending_machines"
    
    # 主键ID
    id = Column(Integer, primary_key=True, index=True, comment="售货机ID")
    
    # 售货机编号/名称
    name = Column(String(100), nullable=False, index=True, comment="售货机名称")
    
    # 设备序列号
    serial_number = Column(String(50), unique=True, nullable=False, index=True, comment="设备序列号")
    
    # 安装位置
    location = Column(String(200), comment="安装位置")
    
    # 区域标识（用于区域定价）
    region = Column(String(50), comment="区域标识")
    
    # 状态：online(在线)，offline(离线)，maintenance(维护中)
    status = Column(String(20), default="offline", comment="设备状态")
    
    # 行数（货道行数）
    row_count = Column(Integer, default=6, comment="货道行数")
    
    # 列数（货道列数）
    column_count = Column(Integer, default=8, comment="货道列数")
    
    # 设备描述
    description = Column(Text, comment="设备描述")
    
    # 创建时间和更新时间
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关系：一个售货机有多个货道
    aisles = relationship("Aisle", back_populates="vending_machine", cascade="all, delete-orphan")
    
    def __repr__(self):
        """字符串表示"""
        return f"<VendingMachine(id={self.id}, name='{self.name}', sn='{self.serial_number}')>"
    
    def get_total_aisles(self):
        """获取售货机总货道数"""
        return self.row_count * self.column_count
