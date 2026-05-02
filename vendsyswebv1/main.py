"""
自动售货机Web系统主入口
使用 FastAPI + SQLite + BootstrapV4 技术栈
"""
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import os

from database import engine, Base, SessionLocal
from routers import auth, devices, products, lanes, commands, status
from utils.security import get_password_hash
from models import User, Device, Product, Firmware

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="自动售货机Web系统",
    description="自动售货机设备管理系统",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件和模板配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(BASE_DIR, "static")
templates_dir = os.path.join(BASE_DIR, "templates")

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

templates = Jinja2Templates(directory=templates_dir) if os.path.exists(templates_dir) else None

# 注册路由
app.include_router(auth.router)
app.include_router(devices.router)
app.include_router(products.router)
app.include_router(lanes.router)
app.include_router(commands.router)
app.include_router(status.router)


def init_test_data():
    """
    初始化测试数据
    在系统启动时创建初始数据
    """
    db = SessionLocal()
    try:
        # 检查是否已有数据
        existing_users = db.query(User).count()
        if existing_users == 0:
            print("正在初始化测试数据...")

            # 创建管理员用户
            admin_user = User(
                username="admin",
                password_hash=get_password_hash("admin123"),
                real_name="系统管理员",
                role="admin",
                email="admin@vending.com",
                phone="13800138000",
                is_active=True
            )
            db.add(admin_user)

            # 创建业务员用户
            sales_user = User(
                username="salesman",
                password_hash=get_password_hash("sales123"),
                real_name="业务员小李",
                role="salesman",
                email="sales@vending.com",
                phone="13800138001",
                is_active=True
            )
            db.add(sales_user)

            # 创建测试商品
            test_products = [
                Product(
                    product_code="COKE001",
                    product_name="可口可乐",
                    product_type="饮料",
                    brand="可口可乐",
                    specification="330ml/罐",
                    unit="罐",
                    price=3.0,
                    cost_price=1.8,
                    original_price=3.5,
                    category="碳酸饮料",
                    sub_category="可乐",
                    description="经典可口可乐，清爽解渴",
                    shelf_life_days=365,
                    storage_condition="冷藏2-8℃",
                    sort_order=1
                ),
                Product(
                    product_code="PEPSI001",
                    product_name="百事可乐",
                    product_type="饮料",
                    brand="百事可乐",
                    specification="330ml/罐",
                    unit="罐",
                    price=3.0,
                    cost_price=1.7,
                    original_price=3.5,
                    category="碳酸饮料",
                    sub_category="可乐",
                    description="百事可乐，新一代选择",
                    shelf_life_days=365,
                    storage_condition="冷藏2-8℃",
                    sort_order=2
                ),
                Product(
                    product_code="SPRITE001",
                    product_name="雪碧",
                    product_type="饮料",
                    brand="可口可乐",
                    specification="330ml/罐",
                    unit="罐",
                    price=3.0,
                    cost_price=1.8,
                    original_price=3.5,
                    category="碳酸饮料",
                    sub_category="柠檬味",
                    description="清爽柠檬味，透心凉",
                    shelf_life_days=365,
                    storage_condition="冷藏2-8℃",
                    sort_order=3
                ),
                Product(
                    product_code="WATER001",
                    product_name="农夫山泉",
                    product_type="饮料",
                    brand="农夫山泉",
                    specification="550ml/瓶",
                    unit="瓶",
                    price=2.0,
                    cost_price=1.0,
                    original_price=2.5,
                    category="饮用水",
                    sub_category="矿泉水",
                    description="天然矿泉水，健康选择",
                    shelf_life_days=730,
                    storage_condition="常温保存",
                    sort_order=4
                ),
                Product(
                    product_code="CHIPS001",
                    product_name="乐事薯片",
                    product_type="零食",
                    brand="乐事",
                    specification="75g/袋",
                    unit="袋",
                    price=8.5,
                    cost_price=4.5,
                    original_price=10.0,
                    category="膨化食品",
                    sub_category="薯片",
                    description="经典原味薯片，香脆可口",
                    shelf_life_days=270,
                    storage_condition="阴凉干燥处",
                    sort_order=5
                ),
                Product(
                    product_code="BISCUIT001",
                    product_name="奥利奥饼干",
                    product_type="零食",
                    brand="奥利奥",
                    specification="116g/盒",
                    unit="盒",
                    price=12.0,
                    cost_price=6.5,
                    original_price=15.0,
                    category="饼干",
                    sub_category="夹心饼干",
                    description="扭一扭，舔一舔，泡一泡",
                    shelf_life_days=270,
                    storage_condition="阴凉干燥处",
                    sort_order=6
                )
            ]
            for product in test_products:
                db.add(product)

            # 创建测试设备
            test_devices = [
                Device(
                    device_code="VM001",
                    device_name="办公楼A座售货机",
                    device_type="综合机",
                    model="VM-2024-Pro",
                    serial_number="SN20240001",
                    firmware_version="v2.1.0",
                    mac_address="00:11:22:33:44:01",
                    location_name="办公楼A座1楼大厅",
                    location_address="北京市朝阳区建国路88号A座1楼",
                    province="北京市",
                    city="北京市",
                    district="朝阳区",
                    longitude=116.4074,
                    latitude=39.9042,
                    contact_person="张经理",
                    contact_phone="13900139001",
                    status="normal",
                    is_active=True
                ),
                Device(
                    device_code="VM002",
                    device_name="办公楼B座售货机",
                    device_type="饮料机",
                    model="VM-2024-Drink",
                    serial_number="SN20240002",
                    firmware_version="v2.0.5",
                    mac_address="00:11:22:33:44:02",
                    location_name="办公楼B座2楼茶水间",
                    location_address="北京市朝阳区建国路88号B座2楼",
                    province="北京市",
                    city="北京市",
                    district="朝阳区",
                    longitude=116.4084,
                    latitude=39.9052,
                    contact_person="李主管",
                    contact_phone="13900139002",
                    status="normal",
                    is_active=True
                ),
                Device(
                    device_code="VM003",
                    device_name="地铁站售货机",
                    device_type="零食机",
                    model="VM-2024-Snack",
                    serial_number="SN20240003",
                    firmware_version="v2.1.0",
                    mac_address="00:11:22:33:44:03",
                    location_name="国贸地铁站B口",
                    location_address="北京市朝阳区国贸地铁站B口",
                    province="北京市",
                    city="北京市",
                    district="朝阳区",
                    longitude=116.4600,
                    latitude=39.9100,
                    contact_person="王站长",
                    contact_phone="13900139003",
                    status="normal",
                    is_active=True
                ),
                Device(
                    device_code="VM004",
                    device_name="大学食堂售货机",
                    device_type="综合机",
                    model="VM-2024-Pro",
                    serial_number="SN20240004",
                    firmware_version="v1.9.0",
                    mac_address="00:11:22:33:44:04",
                    location_name="清华大学学生食堂",
                    location_address="北京市海淀区清华大学紫荆园",
                    province="北京市",
                    city="北京市",
                    district="海淀区",
                    longitude=116.3200,
                    latitude=40.0000,
                    contact_person="赵老师",
                    contact_phone="13900139004",
                    status="maintenance",
                    is_active=True
                ),
                Device(
                    device_code="VM005",
                    device_name="医院门诊售货机",
                    device_type="饮料机",
                    model="VM-2024-Drink",
                    serial_number="SN20240005",
                    firmware_version="v2.1.0",
                    mac_address="00:11:22:33:44:05",
                    location_name="北京协和医院门诊楼",
                    location_address="北京市东城区王府井帅府园1号",
                    province="北京市",
                    city="北京市",
                    district="东城区",
                    longitude=116.4100,
                    latitude=39.9150,
                    contact_person="刘主任",
                    contact_phone="13900139005",
                    status="normal",
                    is_active=True
                )
            ]
            for device in test_devices:
                db.add(device)

            # 创建固件版本
            test_firmware = [
                Firmware(
                    version="v2.1.0",
                    version_name="稳定版 v2.1.0",
                    device_type="全机型",
                    compatible_models="VM-2024-Pro,VM-2024-Drink,VM-2024-Snack",
                    file_name="firmware_v2.1.0.bin",
                    file_path="/firmware/v2.1.0/firmware.bin",
                    file_size=15728640,
                    md5_checksum="a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d",
                    description="修复已知bug，优化网络连接稳定性",
                    change_log="1. 修复4G网络连接不稳定问题\n2. 优化货道电机控制算法\n3. 新增温度传感器校准功能",
                    is_active=True,
                    is_force_update=False,
                    status="release"
                ),
                Firmware(
                    version="v2.0.5",
                    version_name="稳定版 v2.0.5",
                    device_type="全机型",
                    compatible_models="VM-2024-Pro,VM-2024-Drink,VM-2024-Snack",
                    file_name="firmware_v2.0.5.bin",
                    file_path="/firmware/v2.0.5/firmware.bin",
                    file_size=14680064,
                    md5_checksum="b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6",
                    description="紧急修复安全漏洞",
                    change_log="1. 修复安全漏洞\n2. 优化支付流程",
                    is_active=True,
                    is_force_update=True,
                    status="release"
                ),
                Firmware(
                    version="v2.2.0-beta",
                    version_name="测试版 v2.2.0",
                    device_type="测试机型",
                    compatible_models="VM-2024-Pro",
                    file_name="firmware_v2.2.0-beta.bin",
                    file_path="/firmware/v2.2.0-beta/firmware.bin",
                    file_size=16777216,
                    md5_checksum="c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7",
                    description="测试版本，新增AI商品识别功能",
                    change_log="1. 新增AI商品识别功能\n2. 优化用户界面\n3. 新增统计报表功能",
                    is_active=True,
                    is_force_update=False,
                    status="testing"
                )
            ]
            for fw in test_firmware:
                db.add(fw)

            db.commit()
            print("测试数据初始化完成！")
            print("-" * 50)
            print("管理员账号: admin / admin123")
            print("业务员账号: salesman / sales123")
            print("-" * 50)

    except Exception as e:
        print(f"初始化测试数据失败: {e}")
        db.rollback()
    finally:
        db.close()


# 启动时初始化测试数据
init_test_data()


# 页面路由
@app.get("/", response_class=HTMLResponse, tags=["页面"])
async def index(request: Request):
    """首页"""
    if templates:
        return templates.TemplateResponse("login.html", {"request": request})
    return HTMLResponse(content="<h1>自动售货机管理系统</h1><p>请访问 <a href='/docs'>API文档</a> 查看接口</p>")


@app.get("/login", response_class=HTMLResponse, tags=["页面"])
async def login_page(request: Request):
    """登录页面"""
    if templates:
        return templates.TemplateResponse("login.html", {"request": request})
    return HTMLResponse(content="<h1>登录页面</h1>")


@app.get("/dashboard", response_class=HTMLResponse, tags=["页面"])
async def dashboard_page(request: Request):
    """仪表盘页面"""
    if templates:
        return templates.TemplateResponse("dashboard.html", {"request": request})
    return HTMLResponse(content="<h1>仪表盘</h1>")


@app.get("/devices", response_class=HTMLResponse, tags=["页面"])
async def devices_page(request: Request):
    """设备列表页面"""
    if templates:
        return templates.TemplateResponse("devices.html", {"request": request})
    return HTMLResponse(content="<h1>设备管理</h1>")


@app.get("/device/{device_id}", response_class=HTMLResponse, tags=["页面"])
async def device_detail_page(request: Request, device_id: int):
    """设备详情页面"""
    if templates:
        return templates.TemplateResponse("device_detail.html", {"request": request, "device_id": device_id})
    return HTMLResponse(content=f"<h1>设备详情 - ID: {device_id}</h1>")


@app.get("/products", response_class=HTMLResponse, tags=["页面"])
async def products_page(request: Request):
    """商品列表页面"""
    if templates:
        return templates.TemplateResponse("products.html", {"request": request})
    return HTMLResponse(content="<h1>商品管理</h1>")


@app.get("/lanes", response_class=HTMLResponse, tags=["页面"])
async def lanes_page(request: Request):
    """货道管理页面"""
    if templates:
        return templates.TemplateResponse("lanes.html", {"request": request})
    return HTMLResponse(content="<h1>货道管理</h1>")


@app.get("/monitor", response_class=HTMLResponse, tags=["页面"])
async def monitor_page(request: Request):
    """状态监控页面"""
    if templates:
        return templates.TemplateResponse("monitor.html", {"request": request})
    return HTMLResponse(content="<h1>状态监控</h1>")


@app.get("/control", response_class=HTMLResponse, tags=["页面"])
async def control_page(request: Request):
    """远程控制页面"""
    if templates:
        return templates.TemplateResponse("control.html", {"request": request})
    return HTMLResponse(content="<h1>远程控制</h1>")


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "message": "自动售货机系统运行正常"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
