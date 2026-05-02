"""
设备相关的Pydantic模型
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class DeviceBase(BaseModel):
    """设备基础模型"""
    device_code: str = Field(..., max_length=50, description="设备编号")
    device_name: str = Field(..., max_length=100, description="设备名称")
    device_type: Optional[str] = Field(default="普通售货机", max_length=50, description="设备类型")
    model: Optional[str] = Field(None, max_length=50, description="设备型号")
    serial_number: Optional[str] = Field(None, max_length=100, description="设备序列号")
    firmware_version: Optional[str] = Field(None, max_length=50, description="固件版本")
    mac_address: Optional[str] = Field(None, max_length=50, description="MAC地址")

    # 位置信息
    location_name: Optional[str] = Field(None, max_length=200, description="位置名称")
    location_address: Optional[str] = Field(None, max_length=500, description="详细地址")
    province: Optional[str] = Field(None, max_length=50, description="省份")
    city: Optional[str] = Field(None, max_length=50, description="城市")
    district: Optional[str] = Field(None, max_length=50, description="区县")
    longitude: Optional[float] = Field(None, description="经度")
    latitude: Optional[float] = Field(None, description="纬度")

    # 联系人
    contact_person: Optional[str] = Field(None, max_length=50, description="联系人")
    contact_phone: Optional[str] = Field(None, max_length=20, description="联系电话")

    status: Optional[str] = Field(default="normal", max_length=20, description="状态")
    is_active: Optional[bool] = Field(default=True, description="是否激活")
    install_date: Optional[datetime] = Field(None, description="安装日期")


class DeviceCreate(DeviceBase):
    """创建设备请求模型"""
    pass


class DeviceUpdate(BaseModel):
    """更新设备请求模型"""
    device_name: Optional[str] = Field(None, max_length=100)
    device_type: Optional[str] = Field(None, max_length=50)
    model: Optional[str] = Field(None, max_length=50)
    firmware_version: Optional[str] = Field(None, max_length=50)
    location_name: Optional[str] = Field(None, max_length=200)
    location_address: Optional[str] = Field(None, max_length=500)
    province: Optional[str] = Field(None, max_length=50)
    city: Optional[str] = Field(None, max_length=50)
    district: Optional[str] = Field(None, max_length=50)
    longitude: Optional[float] = Field(None)
    latitude: Optional[float] = Field(None)
    contact_person: Optional[str] = Field(None, max_length=50)
    contact_phone: Optional[str] = Field(None, max_length=20)
    status: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = Field(None)


class DeviceStatusResponse(BaseModel):
    """设备状态响应模型"""
    id: int
    device_id: int
    is_online: bool
    last_online_time: Optional[datetime]
    network_type: Optional[str]
    network_quality: Optional[int]
    signal_strength: Optional[int]
    signal_level: Optional[str]
    latency_ms: Optional[int]
    packet_loss_rate: Optional[float]
    ip_address: Optional[str]
    recorded_at: datetime

    class Config:
        from_attributes = True


class DeviceResponse(DeviceBase):
    """设备响应模型"""
    id: int
    created_at: datetime
    updated_at: datetime
    last_status: Optional[DeviceStatusResponse] = Field(None, description="最新状态")

    class Config:
        from_attributes = True
