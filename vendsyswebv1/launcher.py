# -*- coding: utf-8 -*-
"""
最小语法测试
"""
import ast
import os
import sys

print("=" * 60)
print("Python版本:", sys.version)
print("=" * 60)

# 检查所有Python文件
project_dir = os.path.dirname(os.path.abspath(__file__))

# 关键文件列表
critical_files = [
    "routers/lanes.py",
    "main.py",
    "routers/__init__.py",
    "routers/auth.py",
    "routers/devices.py",
    "routers/commands.py",
    "routers/status.py",
    "routers/products.py",
]

print("\n检查关键Python文件的语法...")
print("-" * 60)

all_ok = True
for rel_path in critical_files:
    full_path = os.path.join(project_dir, rel_path)
    
    if not os.path.exists(full_path):
        print(f"[跳过] {rel_path} (文件不存在)")
        continue
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            code = f.read()
        ast.parse(code, filename=rel_path)
        print(f"[OK] {rel_path}")
    except SyntaxError as e:
        print(f"[错误] {rel_path}")
        print(f"       行号: {e.lineno}")
        print(f"       错误: {e.msg}")
        if e.text:
            print(f"       代码: {e.text.strip()}")
        all_ok = False
    except Exception as e:
        print(f"[警告] {rel_path}: {e}")

print("\n" + "-" * 60)
if all_ok:
    print("✅ 所有关键文件语法正确!")
else:
    print("❌ 发现语法错误!")
    sys.exit(1)

# 尝试简化的导入测试
print("\n尝试简化导入测试...")
print("-" * 60)

try:
    # 首先添加到路径
    sys.path.insert(0, project_dir)
    
    print("测试导入 database...")
    import database
    print("  ✅ 成功")
    
    print("测试导入 models...")
    import models
    print("  ✅ 成功")
    
    print("测试导入 schemas...")
    import schemas
    print("  ✅ 成功")
    
    print("测试导入 utils...")
    import utils
    print("  ✅ 成功")
    
    # 测试导入单个router
    print("\n测试导入 routers.auth...")
    import routers.auth
    print("  ✅ 成功")
    
    print("测试导入 routers.devices...")
    import routers.devices
    print("  ✅ 成功")
    
    print("测试导入 routers.products...")
    import routers.products
    print("  ✅ 成功")
    
    print("测试导入 routers.lanes...")
    import routers.lanes
    print("  ✅ 成功")
    
    print("测试导入 routers.commands...")
    import routers.commands
    print("  ✅ 成功")
    
    print("测试导入 routers.status...")
    import routers.status
    print("  ✅ 成功")
    
    print("\n" + "=" * 60)
    print("🎉 所有导入测试通过!")
    print("=" * 60)
    
    # 现在启动
    print("\n启动FastAPI应用...")
    print("  访问地址: http://localhost:8000")
    print("  API文档: http://localhost:8000/docs")
    print("\n按 Ctrl+C 停止服务\n")
    
    import uvicorn
    
    # 如果main.py可以用，从main导入，否则直接构建
    try:
        from main import app
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except Exception as e:
        print(f"从main.py启动失败: {e}")
        print("尝试手动构建...")
        
        from fastapi import FastAPI
        from database import engine, Base
        
        # 创建表
        Base.metadata.create_all(bind=engine)
        
        app = FastAPI(title="自动售货机系统")
        
        # 注册路由
        app.include_router(routers.auth.router)
        app.include_router(routers.devices.router)
        app.include_router(routers.products.router)
        app.include_router(routers.lanes.router)
        app.include_router(routers.commands.router)
        app.include_router(routers.status.router)
        
        @app.get("/health")
        async def health():
            return {"status": "ok"}
        
        uvicorn.run(app, host="0.0.0.0", port=8000)
        
except KeyboardInterrupt:
    print("\n\n服务已停止")
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
