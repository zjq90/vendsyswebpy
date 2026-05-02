"""
命令日志相关的Pydantic模型
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class CommandBase(BaseModel):
    """命令基础模型"""
    command_type: str = Field(..., max_length=50, description="命令类型")
    command_name: Optional[str] = Field(None, max_length=100, description="命令名称")
    command_params: Optional[str] = Field(None, description="命令参数(JSON)")


class CommandCreate(CommandBase):
    """创建命令请求模型"""
    device_id: int = Field(..., description="设备ID")
    firmware_id: Optional[int] = Field(None, description="固件ID")
    firmware_version: Optional[str] = Field(None, max_length=50, description="目标固件版本")


class CommandResponse(CommandBase):
    """命令响应模型"""
    id: int
    device_id: int
    user_id: Optional[int]
    status: str
    result_message: Optional[str]
    sent_at: Optional[datetime]
    executed_at: Optional[datetime]
    completed_at: Optional[datetime]
    firmware_id: Optional[int]
    firmware_version: Optional[str]
    upgrade_progress: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BatchCommandCreate(BaseModel):
    """批量命令创建请求"""
    device_ids: List[int] = Field(..., description="设备ID列表")
    command_type: str = Field(..., max_length=50, description="命令类型")
    command_name: Optional[str] = Field(None, max_length=100, description="命令名称")
    command_params: Optional[str] = Field(None, description="命令参数(JSON)")
