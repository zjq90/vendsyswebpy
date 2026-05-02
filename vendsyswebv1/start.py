# -*- coding: utf-8 -*-
"""
清理缓存并测试语法
"""
import os
import shutil
import sys

def clear_pycache():
    """删除所有__pycache__目录和.pyc文件"""
    project_dir = os.path.dirname(os.path.abspath(__file__))
    deleted_count = 0
    
    for root, dirs, files in os.walk(project_dir):
        # 删除__pycache__目录
        for dir_name in dirs:
            if dir_name == '__pycache__':
                dir_path = os.path.join(root, dir_name)
                try:
                    shutil.rmtree(dir_path)
                    print(f"✓ 已删除: {dir_path}")
                    deleted_count += 1
                except:
                    pass
        
        # 删除.pyc文件
        for file_name in files:
            if file_name.endswith('.pyc'):
                file_path = os.path.join(root, file_name)
                try:
                    os.remove(file_path)
                    print(f"✓ 已删除: {file_path}")
                    deleted_count += 1
                except:
                    pass
    
    return deleted_count

def test_compile(filepath):
    """用py_compile测试文件"""
    import py_compile
    try:
        py_compile.compile(filepath, doraise=True)
        return True, None
    except py_compile.PyCompileError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)

# 主程序
print("=" * 60)
print("清理Python缓存...")
print("=" * 60)

count = clear_pycache()
print(f"\n共删除 {count} 个缓存文件/目录")

print("\n" + "=" * 60)
print("测试语法检查...")
print("=" * 60)

files_to_check = [
    "main.py",
    "database.py",
    "routers/__init__.py",
    "routers/auth.py",
    "routers/devices.py",
    "routers/products.py",
    "routers/lanes.py",
    "routers/commands.py",
    "routers/status.py",
    "models/__init__.py",
    "schemas/__init__.py",
    "utils/__init__.py",
]

all_ok = True
for f in files_to_check:
    if os.path.exists(f):
        ok, msg = test_compile(f)
        if ok:
            print(f"[OK] {f}")
        else:
            print(f"[FAIL] {f}: {msg}")
            all_ok = False
    else:
        print(f"[MISSING] {f}")
        all_ok = False

print("\n" + "=" * 60)
if all_ok:
    print("✅ 所有文件编译通过!")
else:
    print("❌ 存在编译错误!")
    sys.exit(1)

# 尝试导入
print("\n" + "=" * 60)
print("尝试导入模块...")
print("=" * 60)

try:
    print("导入 database...")
    import database
    print("  ✓ 成功")
    
    print("导入 models...")
    import models
    print("  ✓ 成功")
    
    print("导入 schemas...")
    import schemas
    print("  ✓ 成功")
    
    print("导入 utils...")
    import utils
    print("  ✓ 成功")
    
    print("\n导入 routers...")
    print("-" * 60)
    
    print("导入 auth...")
    from routers import auth
    print("  ✓ 成功")
    
    print("导入 devices...")
    from routers import devices
    print("  ✓ 成功")
    
    print("导入 products...")
    from routers import products
    print("  ✓ 成功")
    
    print("导入 lanes...")
    from routers import lanes
    print("  ✓ 成功")
    
    print("导入 commands...")
    from routers import commands
    print("  ✓ 成功")
    
    print("导入 status...")
    from routers import status
    print("  ✓ 成功")
    
    print("\n" + "=" * 60)
    print("🎉 所有模块导入成功!")
    print("=" * 60)
    
    # 初始化数据库和测试数据
    print("\n初始化数据库...")
    from database import engine, Base, SessionLocal
    
    Base.metadata.create_all(bind=engine)
    print("✓ 数据库表已创建")
    
    # 检查测试数据
    db = SessionLocal()
    try:
        from models import User
        user_count = db.query(User).count()
        if user_count == 0:
            print("\n创建测试数据...")
            from utils.security import get_password_hash
            
            # 创建用户
            admin = User(
                username="admin",
                password_hash=get_password_hash("admin123"),
                real_name="系统管理员",
                role="admin",
                email="admin@vending.com"
            )
            db.add(admin)
            
            salesman = User(
                username="salesman",
                password_hash=get_password_hash("sales123"),
                real_name="业务员",
                role="salesman",
                email="sales@vending.com"
            )
            db.add(salesman)
            
            # 创建设备
            from models import Device
            devices = [
                Device(device_code="VM001", device_name="办公楼A座售货机", device_type="综合机", location_name="办公楼A座1楼"),
                Device(device_code="VM002", device_name="办公楼B座售货机", device_type="饮料机", location_name="办公楼B座2楼"),
                Device(device_code="VM003", device_name="地铁站售货机", device_type="零食机", location_name="国贸地铁站"),
            ]
            for d in devices:
                db.add(d)
            
            # 创建商品
            from models import Product
            products = [
                Product(product_code="COKE001", product_name="可口可乐", product_type="饮料", price=3.0),
                Product(product_code="PEPSI001", product_name="百事可乐", product_type="饮料", price=3.0),
                Product(product_code="WATER001", product_name="农夫山泉", product_type="饮料", price=2.0),
            ]
            for p in products:
                db.add(p)
            
            db.commit()
            print("✓ 测试数据已创建")
            print("\n" + "-" * 60)
            print("测试账号:")
            print("  管理员: admin / admin123")
            print("  业务员: salesman / sales123")
            print("-" * 60)
        else:
            print(f"✓ 数据库中已存在 {user_count} 个用户")
    finally:
        db.close()
    
    # 启动服务
    print("\n启动FastAPI服务...")
    print("  服务地址: http://localhost:8000")
    print("  API文档: http://localhost:8000/docs")
    print("\n按 Ctrl+C 停止服务\n")
    
    import uvicorn
    from main import app
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
except KeyboardInterrupt:
    print("\n\n服务已停止")
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
