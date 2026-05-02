import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """
    应用配置类
    使用pydantic-settings管理环境变量
    """
    
    # 应用基本配置
    APP_NAME: str = "自动售货机商品与库存管理系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8080  # 改为8080避免端口冲突
    
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./vending_machine.db"
    
    # 静态文件和模板配置
    STATIC_DIR: str = "static"
    TEMPLATES_DIR: str = "templates"
    
    # 库存阈值配置（默认值）
    DEFAULT_STOCK_THRESHOLD: int = 5
    
    # 分页配置
    DEFAULT_PAGE_SIZE: int = 10
    MAX_PAGE_SIZE: int = 100
    
    class Config:
        """
        配置类的配置
        """
        env_file = ".env"
        case_sensitive = True

# 创建设置实例
settings = Settings()

# 确保必要的目录存在
os.makedirs(settings.STATIC_DIR, exist_ok=True)
os.makedirs(settings.TEMPLATES_DIR, exist_ok=True)
