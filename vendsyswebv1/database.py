"""
数据库配置模块
处理SQLite数据库连接和会话管理
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# 数据库文件路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLALCHEMY_DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'vending_machine.db')}"

# 创建数据库引擎
# check_same_thread: False 允许SQLite在多线程环境中使用
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=True  # 显示SQL日志，生产环境可设为False
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 声明基类，所有模型继承此类
Base = declarative_base()


def get_db():
    """
    数据库会话依赖注入函数
    每次请求创建一个新的数据库会话，请求结束后关闭
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
