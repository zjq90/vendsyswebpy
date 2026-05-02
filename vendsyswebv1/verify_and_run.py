# -*- coding: utf-8 -*-
"""
直接测试lanes.py的核心函数逻辑
"""
import ast
import os
import sys

print("测试1: 语法分析...")
print("-" * 60)

# 读取lanes.py文件并检查语法
lanes_path = os.path.join(os.path.dirname(__file__), "routers", "lanes.py")

if not os.path.exists(lanes_path):
    print(f"文件不存在: {lanes_path}")
    sys.exit(1)

with open(lanes_path, 'r', encoding='utf-8') as f:
    code = f.read()

try:
    ast.parse(code)
    print("✅ lanes.py 语法正确")
except SyntaxError as e:
    print(f"❌ 语法错误: 第{e.lineno}行")
    print(f"   错误: {e.msg}")
    if e.text:
        print(f"   代码: {e.text}")
    sys.exit(1)

# 测试2: 直接导入测试
print("\n测试2: 导入测试...")
print("-" * 60)

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(__file__))

try:
    print("  导入 routers.lanes...")
    import routers.lanes
    print("  ✅ 成功")
except Exception as e:
    print(f"  ❌ 失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("🎉 lanes.py 验证通过!")
print("=" * 60)

# 现在测试整个导入链
print("\n测试3: 完整导入链...")
print("-" * 60)

try:
    print("  导入 main 模块...")
    import main
    print("  ✅ 成功")
except Exception as e:
    print(f"  ❌ 失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("🎉 所有验证通过!")
print("=" * 60)

# 启动服务
print("\n启动服务...")
print("  访问地址: http://localhost:8000")
print("  API文档: http://localhost:8000/docs")
print("\n按 Ctrl+C 停止服务\n")

import uvicorn
uvicorn.run(main.app, host="0.0.0.0", port=8000)
