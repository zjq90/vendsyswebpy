"""
设备模型
定义自动售货机设备的基本信息和投放位置
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Device(Base):
    """
    设备表模型
    存储自动售货机的基本信息和投放位置
    """
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_code = Column(String(50), unique=True, index=True, nullable=False, comment="设备编号")
    device_name = Column(String(100), nullable=False, comment="设备名称")
    device_type = Column(String(50), nullable=True, default="普通售货机", comment="设备类型: 普通售货机, 饮料机, 零食机, 综合机等")
    model = Column(String(50), nullable=True, comment="设备型号")
    serial_number = Column(String(100), unique=True, nullable=True, comment="设备序列号")
    firmware_version = Column(String(50), nullable=True, comment="当前固件版本")
    mac_address = Column(String(50), nullable=True, comment="MAC地址")

    # 投放位置信息
    location_name = Column(String(200), nullable=True, comment="位置名称")
    location_address = Column(String(500), nullable=True, comment="详细地址")
    province = Column(String(50), nullable=True, comment="省份")
    city = Column(String(50), nullable=True, comment="城市")
    district = Column(String(50), nullable=True, comment="区县")
    longitude = Column(Float, nullable=True, comment="经度")
    latitude = Column(Float, nullable=True, comment="纬度")

    # 联系人信息
    contact_person = Column(String(50), nullable=True, comment="联系人")
    contact_phone = Column(String(20), nullable=True, comment="联系电话")

    # 状态信息
    status = Column(String(20), nullable=False, default="normal", comment="状态: normal(正常), maintenance(维护中), offline(离线), faulty(故障)")
    is_active = Column(Boolean, default=True, comment="是否激活")

    # 时间信息
    install_date = Column(DateTime, nullable=True, comment="安装日期")
    last_maintenance_date = Column(DateTime, nullable=True, comment="最后维护日期")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    # 关联关系
    status_history = relationship("DeviceStatus", back_populates="device", cascade="all, delete-orphan")
    hardware_history = relationship("HardwareParams", back_populates="device", cascade="all, delete-orphan")
    lanes = relationship("Lane", back_populates="device", cascade="all, delete-orphan")
    command_logs = relationship("CommandLog", back_populates="device", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Device(id={self.id}, device_code={self.device_code}, device_name={self.device_name})>"
