"""
逐步验证模块导入
"""
import sys

print("="*60)
print("开始验证模块导入...")
print("="*60)

errors = []

# 1. 验证基础模块
try:
    import database
    print("✓ database.py 导入成功")
except Exception as e:
    errors.append(("database", e))
    print(f"✗ database.py 导入失败: {e}")

# 2. 验证utils
try:
    from utils import security
    print("✓ utils/security.py 导入成功")
except Exception as e:
    errors.append(("utils.security", e))
    print(f"✗ utils/security.py 导入失败: {e}")

try:
    from utils import mock_device
    print("✓ utils/mock_device.py 导入成功")
except Exception as e:
    errors.append(("utils.mock_device", e))
    print(f"✗ utils/mock_device.py 导入失败: {e}")

# 3. 验证models
try:
    from models import User
    print("✓ models/user.py 导入成功")
except Exception as e:
    errors.append(("models.user", e))
    print(f"✗ models/user.py 导入失败: {e}")

try:
    from models import Device
    print("✓ models/device.py 导入成功")
except Exception as e:
    errors.append(("models.device", e))
    print(f"✗ models/device.py 导入失败: {e}")

try:
    from models import DeviceStatus
    print("✓ models/device_status.py 导入成功")
except Exception as e:
    errors.append(("models.device_status", e))
    print(f"✗ models/device_status.py 导入失败: {e}")

try:
    from models import HardwareParams
    print("✓ models/hardware_params.py 导入成功")
except Exception as e:
    errors.append(("models.hardware_params", e))
    print(f"✗ models/hardware_params.py 导入失败: {e}")

try:
    from models import Product
    print("✓ models/product.py 导入成功")
except Exception as e:
    errors.append(("models.product", e))
    print(f"✗ models/product.py 导入失败: {e}")

try:
    from models import Lane
    print("✓ models/lane.py 导入成功")
except Exception as e:
    errors.append(("models.lane", e))
    print(f"✗ models/lane.py 导入失败: {e}")

try:
    from models import Firmware
    print("✓ models/firmware.py 导入成功")
except Exception as e:
    errors.append(("models.firmware", e))
    print(f"✗ models/firmware.py 导入失败: {e}")

try:
    from models import CommandLog
    print("✓ models/command_log.py 导入成功")
except Exception as e:
    errors.append(("models.command_log", e))
    print(f"✗ models/command_log.py 导入失败: {e}")

# 4. 验证schemas
try:
    from schemas import UserCreate, UserResponse
    print("✓ schemas/user.py 导入成功")
except Exception as e:
    errors.append(("schemas.user", e))
    print(f"✗ schemas/user.py 导入失败: {e}")

try:
    from schemas import DeviceCreate, DeviceResponse
    print("✓ schemas/device.py 导入成功")
except Exception as e:
    errors.append(("schemas.device", e))
    print(f"✗ schemas/device.py 导入失败: {e}")

try:
    from schemas import ProductCreate, ProductResponse
    print("✓ schemas/product.py 导入成功")
except Exception as e:
    errors.append(("schemas.product", e))
    print(f"✗ schemas/product.py 导入失败: {e}")

try:
    from schemas import LaneCreate, LaneResponse
    print("✓ schemas/lane.py 导入成功")
except Exception as e:
    errors.append(("schemas.lane", e))
    print(f"✗ schemas/lane.py 导入失败: {e}")

# 5. 验证routers
try:
    from routers import auth
    print("✓ routers/auth.py 导入成功")
except Exception as e:
    errors.append(("routers.auth", e))
    print(f"✗ routers/auth.py 导入失败: {e}")

try:
    from routers import devices
    print("✓ routers/devices.py 导入成功")
except Exception as e:
    errors.append(("routers.devices", e))
    print(f"✗ routers/devices.py 导入失败: {e}")

try:
    from routers import products
    print("✓ routers/products.py 导入成功")
except Exception as e:
    errors.append(("routers.products", e))
    print(f"✗ routers/products.py 导入失败: {e}")

try:
    from routers import lanes
    print("✓ routers/lanes.py 导入成功")
except Exception as e:
    errors.append(("routers.lanes", e))
    print(f"✗ routers/lanes.py 导入失败: {e}")

try:
    from routers import commands
    print("✓ routers/commands.py 导入成功")
except Exception as e:
    errors.append(("routers.commands", e))
    print(f"✗ routers/commands.py 导入失败: {e}")

try:
    from routers import status
    print("✓ routers/status.py 导入成功")
except Exception as e:
    errors.append(("routers.status", e))
    print(f"✗ routers/status.py 导入失败: {e}")

print("="*60)
if errors:
    print(f"❌ 发现 {len(errors)} 个导入错误:")
    for name, e in errors:
        print(f"   - {name}: {e}")
    sys.exit(1)
else:
    print("✅ 所有模块导入成功！")
    print("="*60)
    print("尝试创建数据库表...")
    
    try:
        from database import engine, Base
        Base.metadata.create_all(bind=engine)
        print("✅ 数据库表创建成功！")
        
        # 测试数据初始化
        print("="*60)
        print("尝试初始化测试数据...")
        
        from sqlalchemy.orm import sessionmaker
        from models import User
        from utils.security import get_password_hash
        
        Session = sessionmaker(bind=engine)
        db = Session()
        
        try:
            existing = db.query(User).count()
            if existing == 0:
                print("正在创建测试用户...")
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
                
                db.commit()
                print("✅ 测试用户创建成功！")
                print("   管理员: admin / admin123")
                print("   业务员: salesman / sales123")
            else:
                print(f"数据库中已存在 {existing} 个用户，跳过创建")
        finally:
            db.close()
            
    except Exception as e:
        print(f"✗ 数据库操作失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

print("="*60)
print("🎉 验证完成！所有模块准备就绪")
print("="*60)
