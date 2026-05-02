"""
固件相关的Pydantic模型
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class FirmwareBase(BaseModel):
    """固件基础模型"""
    version: str = Field(..., max_length=50, description="固件版本号")
    version_name: Optional[str] = Field(None, max_length=100, description="版本名称")
    device_type: Optional[str] = Field(None, max_length=50, description="适用设备类型")
    compatible_models: Optional[str] = Field(None, max_length=500, description="兼容型号列表")
    file_name: str = Field(..., max_length=200, description="固件文件名")
    file_path: str = Field(..., max_length=500, description="文件存储路径")
    file_size: Optional[int] = Field(None, description="文件大小")
    md5_checksum: Optional[str] = Field(None, max_length=32, description="MD5校验值")
    release_date: Optional[datetime] = Field(None, description="发布日期")
    description: Optional[str] = Field(None, description="版本描述")
    change_log: Optional[str] = Field(None, description="更新日志")
    is_active: Optional[bool] = Field(default=True, description="是否启用")
    is_force_update: Optional[bool] = Field(default=False, description="是否强制更新")
    status: Optional[str] = Field(default="testing", max_length=20, description="状态")


class FirmwareCreate(FirmwareBase):
    """创建固件请求模型"""
    pass


class FirmwareResponse(FirmwareBase):
    """固件响应模型"""
    id: int
    download_count: int
    update_success_count: int
    update_fail_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
