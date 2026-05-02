from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager

from models.database import init_db, get_db
from routers import auth, roles, permissions, franchisees, users, logs, configs, dashboard


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    """
    # 启动时初始化数据库
    init_db()
    print("数据库初始化完成")
    yield
    # 关闭时的清理操作
    print("应用关闭")


# 创建FastAPI应用
app = FastAPI(
    title="自动售货机管理系统",
    description="自动售货机Web系统 - 系统管理与权限控制模块",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# 确保目录存在
STATIC_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# 注册路由
app.include_router(auth.router)
app.include_router(roles.router)
app.include_router(permissions.router)
app.include_router(franchisees.router)
app.include_router(users.router)
app.include_router(logs.router)
app.include_router(configs.router)
app.include_router(dashboard.router)


# 异常处理
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    处理参数验证错误
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "code": 422,
            "message": "参数验证失败",
            "details": str(exc.errors())
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    全局异常处理
    """
    import traceback
    traceback.print_exc()
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": 500,
            "message": "服务器内部错误",
            "details": str(exc)
        }
    )


# 健康检查接口
@app.get("/health", tags=["系统"])
async def health_check():
    """
    健康检查接口
    """
    return {"status": "healthy", "message": "服务运行正常"}


# 根路径 - 重定向到登录页
@app.get("/", response_class=HTMLResponse, tags=["页面"])
async def root():
    """
    根路径 - 跳转到登录页
    """
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta http-equiv="refresh" content="0; url=/static/login.html">
        <title>自动售货机管理系统</title>
    </head>
    <body>
        <p>正在跳转到登录页...</p>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
