# -*- coding: utf-8 -*-
"""
简单的语法验证器
"""
import ast
import os
import sys

print("=" * 60)
print("语法验证中...")
print("=" * 60)

# 检查routers/lanes.py
files_to_check = [
    "routers/lanes.py",
]

all_ok = True
for filepath in files_to_check:
    if os.path.exists(filepath):
        print(f"\n检查: {filepath}")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                code = f.read()
            ast.parse(code, filename=filepath)
            print(f"  ✅ 语法正确")
        except SyntaxError as e:
            print(f"  ❌ 语法错误!")
            print(f"     行号: {e.lineno}")
            print(f"     错误: {e.msg}")
            if e.text:
                print(f"     代码: {e.text.strip()}")
            all_ok = False
    else:
        print(f"  ⚠️ 文件不存在: {filepath}")
        all_ok = False

if not all_ok:
    print("\n" + "=" * 60)
    print("❌ 发现语法错误")
    print("=" * 60)
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ 所有文件语法正确!")
print("=" * 60)

# 现在尝试导入
print("\n尝试导入模块...")
print("-" * 60)

try:
    print("导入 database...")
    import database
    print("  ✅ 成功")

    print("导入 models...")
    import models
    print("  ✅ 成功")

    print("导入 schemas...")
    import schemas
    print("  ✅ 成功")

    print("导入 utils...")
    import utils
    print("  ✅ 成功")

    print("\n导入 routers...")
    print("-" * 60)
    
    print("导入 routers.auth...")
    from routers import auth
    print("  ✅ 成功")
    
    print("导入 routers.devices...")
    from routers import devices
    print("  ✅ 成功")
    
    print("导入 routers.products...")
    from routers import products
    print("  ✅ 成功")
    
    print("导入 routers.lanes...")
    from routers import lanes
    print("  ✅ 成功")
    
    print("导入 routers.commands...")
    from routers import commands
    print("  ✅ 成功")
    
    print("导入 routers.status...")
    from routers import status
    print("  ✅ 成功")

    print("\n" + "=" * 60)
    print("🎉 所有模块导入成功!")
    print("=" * 60)

    # 现在启动应用
    print("\n启动FastAPI应用...")
    print("  服务地址: http://localhost:8000")
    print("  API文档: http://localhost:8000/docs")
    print("\n按 Ctrl+C 停止服务\n")

    import uvicorn
    
    # 从main.py导入app
    from main import app
    
    uvicorn.run(app, host="0.0.0.0", port=8000)

except KeyboardInterrupt:
    print("\n\n服务已停止")
    sys.exit(0)
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
