"""
数据库连接管理模块
处理数据库连接池和会话管理
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
    AsyncEngine
)
from config import settings
from models import Base


class DatabaseManager:
    """
    数据库管理器类
    负责管理数据库连接池和会话
    """
    
    _instance = None
    _engine: AsyncEngine = None
    _async_session_maker: async_sessionmaker = None
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_engine(cls) -> AsyncEngine:
        """
        获取数据库引擎
        
        Returns:
            AsyncEngine: 异步数据库引擎
        """
        if cls._engine is None:
            cls._engine = create_async_engine(
                settings.DATABASE_URL,
                echo=settings.DEBUG,  # 调试模式下打印SQL语句
                future=True,
                # SQLite连接池配置
                pool_pre_ping=True
            )
        return cls._engine
    
    @classmethod
    def get_async_session(cls) -> async_sessionmaker:
        """
        获取异步会话工厂
        
        Returns:
            async_sessionmaker: 异步会话工厂
        """
        if cls._async_session_maker is None:
            engine = cls.get_engine()
            cls._async_session_maker = async_sessionmaker(
                engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False
            )
        return cls._async_session_maker
    
    @classmethod
    async def init_db(cls, drop_tables: bool = False) -> None:
        """
        初始化数据库表
        
        Args:
            drop_tables: 是否先删除已存在的表（开发环境使用）
        """
        engine = cls.get_engine()
        
        async with engine.begin() as conn:
            if drop_tables:
                # 开发环境：先删除所有表
                await conn.run_sync(Base.metadata.drop_all)
            # 创建所有表
            await conn.run_sync(Base.metadata.create_all)
    
    @classmethod
    async def close_db(cls) -> None:
        """关闭数据库连接"""
        if cls._engine is not None:
            await cls._engine.dispose()
            cls._engine = None
            cls._async_session_maker = None


# 全局数据库管理器实例
db_manager = DatabaseManager()


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    获取异步数据库会话（用于FastAPI依赖注入）
    
    Yields:
        AsyncSession: 数据库会话
    """
    async_session = db_manager.get_async_session()
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_session_context() -> AsyncGenerator[AsyncSession, None]:
    """
    异步上下文管理器模式获取会话
    
    用法：
        async with get_session_context() as session:
            result = await session.execute(...)
    """
    async_session = db_manager.get_async_session()
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
