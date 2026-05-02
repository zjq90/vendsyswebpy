"""
系统配置模块
包含数据库连接、应用设置等配置信息
"""
import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    全局设置类
    继承自BaseSettings，支持从环境变量读取配置
    """
    
    # 应用基础配置
    APP_NAME: str = "自动售货机订单交易管理系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # 数据库配置
    DATABASE_URL: str = "sqlite+aiosqlite:///./vending_machine.db"
    
    # 服务配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # API配置
    API_PREFIX: str = "/api"
    
    # 静态文件配置
    STATIC_DIR: str = "static"
    TEMPLATES_DIR: str = "templates"
    
    # 分页配置
    DEFAULT_PAGE_SIZE: int = 10
    MAX_PAGE_SIZE: int = 100
    
    # 支付平台配置
    # 这里只是示例配置，实际使用时需要从环境变量或配置文件读取
    WECHAT_APP_ID: Optional[str] = None
    WECHAT_MCH_ID: Optional[str] = None
    ALIPAY_APP_ID: Optional[str] = None
    
    class Config:
        """Pydantic配置类"""
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"


# 创建设置实例
settings = Settings()


def get_project_root() -> str:
    """
    获取项目根目录路径
    
    Returns:
        str: 项目根目录的绝对路径
    """
    return os.path.dirname(os.path.abspath(__file__))


def get_static_dir() -> str:
    """
    获取静态文件目录路径
    
    Returns:
        str: 静态文件目录的绝对路径
    """
    return os.path.join(get_project_root(), settings.STATIC_DIR)


def get_templates_dir() -> str:
    """
    获取模板文件目录路径
    
    Returns:
        str: 模板文件目录的绝对路径
    """
    return os.path.join(get_project_root(), settings.TEMPLATES_DIR)


def get_database_path() -> str:
    """
    获取数据库文件路径（从DATABASE_URL解析）
    
    Returns:
        str: 数据库文件的绝对路径
    """
    # 从sqlite+aiosqlite:///./vending_machine.db中提取路径
    url = settings.DATABASE_URL
    if url.startswith("sqlite+aiosqlite:///"):
        db_path = url.replace("sqlite+aiosqlite:///", "")
        if not os.path.isabs(db_path):
            db_path = os.path.join(get_project_root(), db_path)
        return db_path
    return os.path.join(get_project_root(), "vending_machine.db")
