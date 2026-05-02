"""
直接验证语法并启动测试
"""
import sys
import os

# 首先验证routers/lanes.py的语法
print("验证语法...")
print("-" * 60)

import ast

files_to_check = [
    "routers/lanes.py",
    "main.py",
]

all_ok = True
for fp in files_to_check:
    if os.path.exists(fp):
        try:
            with open(fp, "r", encoding="utf-8") as f:
                code = f.read()
            ast.parse(code, filename=fp)
            print(f"✅ {fp} 语法正确")
        except SyntaxError as e:
            print(f"❌ {fp} 语法错误:")
            print(f"   行号: {e.lineno}")
            print(f"   错误: {e.msg}")
            if e.text:
                print(f"   代码: {e.text}")
            all_ok = False
    else:
        print(f"⚠️ {fp} 文件不存在")

if not all_ok:
    print("\n❌ 语法检查失败，退出")
    sys.exit(1)

print("\n" + "-" * 60)
print("语法检查通过！尝试导入模块...")
print("-" * 60)

# 现在尝试简化的导入
try:
    # 从数据库开始，逐步验证
    print("导入 database...")
    import database
    print("✅ database 导入成功")

    print("导入 models...")
    import models
    print("✅ models 导入成功")

    print("导入 schemas...")
    import schemas
    print("✅ schemas 导入成功")

    print("导入 utils...")
    import utils
    print("✅ utils 导入成功")

    # 逐个导入routers，找出问题所在
    print("\n导入 routers/auth...")
    from routers import auth
    print("✅ routers/auth 导入成功")

    print("导入 routers/devices...")
    from routers import devices
    print("✅ routers/devices 导入成功")

    print("导入 routers/products...")
    from routers import products
    print("✅ routers/products 导入成功")

    print("导入 routers/lanes...")
    from routers import lanes
    print("✅ routers/lanes 导入成功")

    print("导入 routers/commands...")
    from routers import commands
    print("✅ routers/commands 导入成功")

    print("导入 routers/status...")
    from routers import status
    print("✅ routers/status 导入成功")

except Exception as e:
    print(f"\n❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("🎉 所有模块导入成功！")
print("=" * 60)
print("\n现在启动FastAPI应用...")

try:
    # 重新读取main.py中的初始化逻辑
    from database import engine, Base, SessionLocal
    from utils.security import get_password_hash
    from models import User, Device, Product, Firmware

    # 创建表
    print("\n创建数据库表...")
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表已创建")

    # 初始化测试数据
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            print("\n初始化测试数据...")
            
            # 创建用户
            db.add(User(
                username="admin",
                password_hash=get_password_hash("admin123"),
                real_name="系统管理员",
                role="admin",
                email="admin@vending.com",
                phone="13800138000"
            ))
            db.add(User(
                username="salesman",
                password_hash=get_password_hash("sales123"),
                real_name="业务员小李",
                role="salesman",
                email="sales@vending.com",
                phone="13800138001"
            ))

            # 创建商品
            products = [
                Product(product_code="COKE001", product_name="可口可乐", product_type="饮料", price=3.0, category="碳酸饮料"),
                Product(product_code="PEPSI001", product_name="百事可乐", product_type="饮料", price=3.0, category="碳酸饮料"),
                Product(product_code="WATER001", product_name="农夫山泉", product_type="饮料", price=2.0, category="饮用水"),
                Product(product_code="CHIPS001", product_name="乐事薯片", product_type="零食", price=8.5, category="膨化食品"),
            ]
            for p in products:
                db.add(p)

            # 创建设备
            devices = [
                Device(device_code="VM001", device_name="办公楼A座售货机", device_type="综合机", 
                       location_name="办公楼A座1楼", status="normal"),
                Device(device_code="VM002", device_name="办公楼B座售货机", device_type="饮料机",
                       location_name="办公楼B座2楼", status="normal"),
                Device(device_code="VM003", device_name="地铁站售货机", device_type="零食机",
                       location_name="国贸地铁站", status="normal"),
            ]
            for d in devices:
                db.add(d)

            db.commit()
            print("✅ 测试数据初始化完成")
            print("\n" + "-" * 60)
            print("测试账号:")
            print("  管理员: admin / admin123")
            print("  业务员: salesman / sales123")
            print("-" * 60)
        else:
            print("✅ 数据库中已有数据，跳过初始化")
    finally:
        db.close()

    print("\n🚀 启动Web服务...")
    print("   访问地址: http://localhost:8000")
    print("   API文档: http://localhost:8000/docs")
    print("\n按 Ctrl+C 停止服务\n")

    import uvicorn
    from main import app
    uvicorn.run(app, host="0.0.0.0", port=8000)

except KeyboardInterrupt:
    print("\n服务已停止")
except Exception as e:
    print(f"\n❌ 启动失败: {e}")
    import traceback
    traceback.print_exc()
