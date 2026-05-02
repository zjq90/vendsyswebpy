# 简单验证测试
import sys
import traceback

def test_imports():
    print("正在验证模块导入...")
    errors = []
    
    # 按依赖顺序导入
    modules_to_test = [
        "database",
        "utils.security",
        "utils.mock_device",
        "models.user",
        "models.device",
        "models.device_status",
        "models.hardware_params",
        "models.product",
        "models.lane",
        "models.firmware",
        "models.command_log",
        "models",
        "schemas.user",
        "schemas.device",
        "schemas.hardware",
        "schemas.product",
        "schemas.lane",
        "schemas.firmware",
        "schemas.command",
        "schemas",
        "routers.auth",
        "routers.devices",
        "routers.products",
        "routers.lanes",
        "routers.commands",
        "routers.status",
        "routers",
        "main"
    ]
    
    for module_name in modules_to_test:
        try:
            __import__(module_name)
            print(f"  ✓ {module_name}")
        except Exception as e:
            errors.append((module_name, e))
            print(f"  ✗ {module_name}: {e}")
            traceback.print_exc()
    
    if errors:
        print(f"\n❌ 发现 {len(errors)} 个错误")
        for name, err in errors:
            print(f"  - {name}: {err}")
        return False
    else:
        print("\n✅ 所有模块导入成功！")
        return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
