import ast
import os
import sys

def check_syntax(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
        ast.parse(code)
        return True, None
    except SyntaxError as e:
        return False, f"语法错误: {e.msg}，行号: {e.lineno}"
    except Exception as e:
        return False, f"错误: {str(e)}"

# 检查关键文件
files_to_check = [
    "main.py",
    "database.py",
    "models/__init__.py",
    "models/user.py",
    "models/device.py",
    "models/device_status.py",
    "models/hardware_params.py",
    "models/product.py",
    "models/lane.py",
    "models/firmware.py",
    "models/command_log.py",
    "schemas/__init__.py",
    "schemas/user.py",
    "schemas/device.py",
    "schemas/hardware.py",
    "schemas/product.py",
    "schemas/lane.py",
    "schemas/firmware.py",
    "schemas/command.py",
    "routers/__init__.py",
    "routers/auth.py",
    "routers/devices.py",
    "routers/products.py",
    "routers/lanes.py",
    "routers/commands.py",
    "routers/status.py",
    "utils/__init__.py",
    "utils/security.py",
    "utils/mock_device.py",
]

print("检查Python文件语法...")
print("="*50)

all_passed = True
for filepath in files_to_check:
    if os.path.exists(filepath):
        ok, msg = check_syntax(filepath)
        if ok:
            print(f"[OK] {filepath}")
        else:
            print(f"[FAIL] {filepath} - {msg}")
            all_passed = False
    else:
        print(f"[SKIP] {filepath} - 文件不存在")

print("="*50)
if all_passed:
    print("✅ 所有Python文件语法检查通过！")
else:
    print("❌ 发现语法错误！")
    sys.exit(1)
