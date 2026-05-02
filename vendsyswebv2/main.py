"""
自动售货机商品与库存管理系统
主应用入口文件
"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    在应用启动时初始化数据库
    """
    print(f"正在启动 {settings.APP_NAME}...")
    print(f"版本: {settings.APP_VERSION}")
    
    # 延迟导入以避免循环导入
    from app.utils.init_data import init_database
    init_database()
    print("数据库初始化完成")
    
    yield
    
    print("应用关闭中...")


# 创建FastAPI应用实例
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="自动售货机商品与库存管理系统API",
    lifespan=lifespan,
)

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境允许所有来源，生产环境应配置具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")

# 配置模板引擎
templates = Jinja2Templates(directory=settings.TEMPLATES_DIR)

# 延迟导入路由以避免循环导入
from app.routers import api_router
app.include_router(api_router, prefix="/api")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """
    首页 - 仪表板
    """
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/products", response_class=HTMLResponse)
async def products_page(request: Request):
    """
    商品管理页面
    """
    return templates.TemplateResponse("products.html", {"request": request})


@app.get("/vending-machines", response_class=HTMLResponse)
async def vending_machines_page(request: Request):
    """
    售货机管理页面
    """
    return templates.TemplateResponse("vending_machines.html", {"request": request})


@app.get("/inventory", response_class=HTMLResponse)
async def inventory_page(request: Request):
    """
    库存管理页面
    """
    return templates.TemplateResponse("inventory.html", {"request": request})


@app.get("/replenishment", response_class=HTMLResponse)
async def replenishment_page(request: Request):
    """
    补货管理页面
    """
    return templates.TemplateResponse("replenishment.html", {"request": request})


@app.get("/price-strategies", response_class=HTMLResponse)
async def price_strategies_page(request: Request):
    """
    价格策略管理页面
    """
    return templates.TemplateResponse("price_strategies.html", {"request": request})


@app.get("/init-test-data")
async def init_test_data():
    """
    初始化测试数据接口
    访问此URL可以初始化数据库并生成测试数据
    """
    try:
        from app.utils.init_data import init_database, generate_test_data
        init_database()
        generate_test_data()
        return {"success": True, "message": "测试数据初始化完成"}
    except Exception as e:
        return {"success": False, "message": f"初始化失败: {str(e)}"}


if __name__ == "__main__":
    import uvicorn
    
    print(f"启动 {settings.APP_NAME} 服务...")
    print(f"访问地址: http://localhost:{settings.PORT}")
    print(f"API文档: http://localhost:{settings.PORT}/docs")
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
