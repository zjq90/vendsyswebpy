"""
数据库初始化和测试数据生成脚本
用于初始化数据库表并生成测试数据
"""

import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal
import random

# 添加项目路径到sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.database import (
    init_db, SessionLocal,
    Role, Permission, RolePermission,
    Franchisee, User, SystemConfig,
    Device, Transaction
)
from utils.auth import hash_password


def create_permissions(db):
    """
    创建权限菜单数据
    """
    print("正在创建权限菜单...")
    
    # 权限列表（菜单和按钮权限）
    permissions_data = [
        # 一级菜单
        {"name": "仪表盘", "code": "dashboard", "type": "menu", "parent_id": None, "path": "index.html", "icon": "fas fa-tachometer-alt", "sort_order": 1},
        
        # 系统管理菜单
        {"name": "系统管理", "code": "system", "type": "menu", "parent_id": None, "path": None, "icon": "fas fa-cog", "sort_order": 10},
        
        # 角色管理（子菜单）
        {"name": "角色管理", "code": "role", "type": "menu", "parent_id": None, "path": "roles.html", "icon": "fas fa-user-tag", "sort_order": 11},
        {"name": "查看角色", "code": "role:view", "type": "button", "parent_id": None, "sort_order": 111},
        {"name": "新增角色", "code": "role:create", "type": "button", "parent_id": None, "sort_order": 112},
        {"name": "编辑角色", "code": "role:update", "type": "button", "parent_id": None, "sort_order": 113},
        {"name": "删除角色", "code": "role:delete", "type": "button", "parent_id": None, "sort_order": 114},
        {"name": "分配权限", "code": "role:permission", "type": "button", "parent_id": None, "sort_order": 115},
        
        # 用户管理（子菜单）
        {"name": "用户管理", "code": "user", "type": "menu", "parent_id": None, "path": "users.html", "icon": "fas fa-users", "sort_order": 12},
        {"name": "查看用户", "code": "user:view", "type": "button", "parent_id": None, "sort_order": 121},
        {"name": "新增用户", "code": "user:create", "type": "button", "parent_id": None, "sort_order": 122},
        {"name": "编辑用户", "code": "user:update", "type": "button", "parent_id": None, "sort_order": 123},
        {"name": "删除用户", "code": "user:delete", "type": "button", "parent_id": None, "sort_order": 124},
        {"name": "重置密码", "code": "user:resetpwd", "type": "button", "parent_id": None, "sort_order": 125},
        
        # 加盟商管理（子菜单）
        {"name": "加盟商管理", "code": "franchisee", "type": "menu", "parent_id": None, "path": "franchisees.html", "icon": "fas fa-building", "sort_order": 13},
        {"name": "查看加盟商", "code": "franchisee:view", "type": "button", "parent_id": None, "sort_order": 131},
        {"name": "新增加盟商", "code": "franchisee:create", "type": "button", "parent_id": None, "sort_order": 132},
        {"name": "编辑加盟商", "code": "franchisee:update", "type": "button", "parent_id": None, "sort_order": 133},
        {"name": "删除加盟商", "code": "franchisee:delete", "type": "button", "parent_id": None, "sort_order": 134},
        
        # 操作日志（子菜单）
        {"name": "操作日志", "code": "log", "type": "menu", "parent_id": None, "path": "logs.html", "icon": "fas fa-history", "sort_order": 14},
        {"name": "查看日志", "code": "log:view", "type": "button", "parent_id": None, "sort_order": 141},
        {"name": "清理日志", "code": "log:clear", "type": "button", "parent_id": None, "sort_order": 142},
        
        # 系统配置（子菜单）
        {"name": "系统配置", "code": "config", "type": "menu", "parent_id": None, "path": "configs.html", "icon": "fas fa-sliders-h", "sort_order": 15},
        {"name": "查看配置", "code": "config:view", "type": "button", "parent_id": None, "sort_order": 151},
        {"name": "新增配置", "code": "config:create", "type": "button", "parent_id": None, "sort_order": 152},
        {"name": "编辑配置", "code": "config:update", "type": "button", "parent_id": None, "sort_order": 153},
        {"name": "删除配置", "code": "config:delete", "type": "button", "parent_id": None, "sort_order": 154},
    ]
    
    # 检查权限是否已存在
    existing_codes = set()
    existing = db.query(Permission).all()
    for p in existing:
        existing_codes.add(p.code)
    
    # 创建权限
    created_count = 0
    for p_data in permissions_data:
        if p_data["code"] not in existing_codes:
            permission = Permission(
                name=p_data["name"],
                code=p_data["code"],
                type=p_data["type"],
                parent_id=p_data.get("parent_id"),
                path=p_data.get("path"),
                icon=p_data.get("icon"),
                sort_order=p_data.get("sort_order", 0),
                is_active=True
            )
            db.add(permission)
            created_count += 1
    
    db.commit()
    print(f"  已创建 {created_count} 个权限")
    
    # 返回权限列表，用于后续分配
    all_permissions = db.query(Permission).all()
    return {p.code: p for p in all_permissions}


def create_roles(db, permissions_dict):
    """
    创建角色数据
    """
    print("正在创建角色...")
    
    # 检查角色是否已存在
    existing_roles = db.query(Role).all()
    existing_codes = {r.code for r in existing_roles}
    
    # 角色列表
    roles_data = [
        {
            "name": "超级管理员",
            "code": "super_admin",
            "description": "拥有系统所有权限，可管理所有功能",
            "is_system": True,
            "permissions": list(permissions_dict.keys())  # 所有权限
        },
        {
            "name": "运营经理",
            "code": "operator",
            "description": "负责日常运营管理，包括设备监控、订单管理等",
            "is_system": True,
            "permissions": [
                "dashboard",
                "user", "user:view",
                "franchisee", "franchisee:view",
                "log", "log:view"
            ]
        },
        {
            "name": "运维人员",
            "code": "maintainer",
            "description": "负责设备维护和故障处理",
            "is_system": True,
            "permissions": [
                "dashboard",
                "franchisee", "franchisee:view"
            ]
        },
        {
            "name": "财务人员",
            "code": "finance",
            "description": "负责财务数据查看和对账",
            "is_system": True,
            "permissions": [
                "dashboard",
                "log", "log:view"
            ]
        },
        {
            "name": "加盟商管理员",
            "code": "franchisee_admin",
            "description": "加盟商账号，只能管理自己的设备和数据",
            "is_system": True,
            "permissions": [
                "dashboard",
                "franchisee", "franchisee:view"
            ]
        }
    ]
    
    created_count = 0
    for r_data in roles_data:
        if r_data["code"] not in existing_codes:
            role = Role(
                name=r_data["name"],
                code=r_data["code"],
                description=r_data["description"],
                is_system=r_data["is_system"],
                is_active=True
            )
            db.add(role)
            db.flush()  # 获取role.id
            
            # 分配权限
            for perm_code in r_data["permissions"]:
                if perm_code in permissions_dict:
                    role_perm = RolePermission(
                        role_id=role.id,
                        permission_id=permissions_dict[perm_code].id
                    )
                    db.add(role_perm)
            
            created_count += 1
    
    db.commit()
    print(f"  已创建 {created_count} 个角色")
    
    # 返回角色列表
    all_roles = db.query(Role).all()
    return {r.code: r for r in all_roles}


def create_franchisees(db):
    """
    创建加盟商数据（多级结构）
    """
    print("正在创建加盟商...")
    
    # 检查是否已有数据
    existing_count = db.query(Franchisee).count()
    if existing_count > 0:
        print("  加盟商数据已存在，跳过")
        # 返回现有数据
        all_franchisees = db.query(Franchisee).all()
        return {f.code: f for f in all_franchisees}
    
    # 一级加盟商（总代理商）
    franchisees_data = [
        # 一级
        {"name": "华东运营中心", "code": "FRANCHISEE_001", "type": "agent", "level": 1, "parent_id": None,
         "contact_person": "张三", "contact_phone": "13800138001", "contact_email": "zhang@example.com",
         "address": "上海市浦东新区张江高科技园区"},
        
        {"name": "华北运营中心", "code": "FRANCHISEE_002", "type": "agent", "level": 1, "parent_id": None,
         "contact_person": "李四", "contact_phone": "13800138002", "contact_email": "li@example.com",
         "address": "北京市海淀区中关村软件园"},
        
        {"name": "华南运营中心", "code": "FRANCHISEE_003", "type": "agent", "level": 1, "parent_id": None,
         "contact_person": "王五", "contact_phone": "13800138003", "contact_email": "wang@example.com",
         "address": "广州市天河区珠江新城"},
    ]
    
    # 先创建一级加盟商
    created_ids = {}
    for f_data in franchisees_data:
        franchisee = Franchisee(
            name=f_data["name"],
            code=f_data["code"],
            type=f_data["type"],
            level=f_data["level"],
            parent_id=f_data.get("parent_id"),
            contact_person=f_data.get("contact_person"),
            contact_phone=f_data.get("contact_phone"),
            contact_email=f_data.get("contact_email"),
            address=f_data.get("address"),
            is_active=True
        )
        db.add(franchisee)
        db.flush()
        created_ids[f_data["code"]] = franchisee.id
    
    # 二级加盟商
    second_level_data = [
        {"name": "上海静安分公司", "code": "FRANCHISEE_001_01", "type": "franchisee", "level": 2,
         "parent_code": "FRANCHISEE_001",
         "contact_person": "赵六", "contact_phone": "13800138011", "address": "上海市静安区南京西路"},
        
        {"name": "杭州分公司", "code": "FRANCHISEE_001_02", "type": "franchisee", "level": 2,
         "parent_code": "FRANCHISEE_001",
         "contact_person": "钱七", "contact_phone": "13800138012", "address": "杭州市西湖区文三路"},
        
        {"name": "北京朝阳分公司", "code": "FRANCHISEE_002_01", "type": "franchisee", "level": 2,
         "parent_code": "FRANCHISEE_002",
         "contact_person": "孙八", "contact_phone": "13800138021", "address": "北京市朝阳区建国路"},
        
        {"name": "深圳分公司", "code": "FRANCHISEE_003_01", "type": "franchisee", "level": 2,
         "parent_code": "FRANCHISEE_003",
         "contact_person": "周九", "contact_phone": "13800138031", "address": "深圳市南山区科技园"},
    ]
    
    for f_data in second_level_data:
        franchisee = Franchisee(
            name=f_data["name"],
            code=f_data["code"],
            type=f_data["type"],
            level=f_data["level"],
            parent_id=created_ids[f_data["parent_code"]],
            contact_person=f_data.get("contact_person"),
            contact_phone=f_data.get("contact_phone"),
            address=f_data.get("address"),
            is_active=True
        )
        db.add(franchisee)
        db.flush()
        created_ids[f_data["code"]] = franchisee.id
    
    # 三级加盟商
    third_level_data = [
        {"name": "静安南京西路店", "code": "FRANCHISEE_001_01_01", "type": "franchisee", "level": 3,
         "parent_code": "FRANCHISEE_001_01",
         "contact_person": "吴十", "contact_phone": "13800138111"},
    ]
    
    for f_data in third_level_data:
        franchisee = Franchisee(
            name=f_data["name"],
            code=f_data["code"],
            type=f_data["type"],
            level=f_data["level"],
            parent_id=created_ids[f_data["parent_code"]],
            contact_person=f_data.get("contact_person"),
            contact_phone=f_data.get("contact_phone"),
            is_active=True
        )
        db.add(franchisee)
        db.flush()
        created_ids[f_data["code"]] = franchisee.id
    
    db.commit()
    print(f"  已创建 {len(franchisees_data) + len(second_level_data) + len(third_level_data)} 个加盟商")
    
    # 返回所有加盟商
    all_franchisees = db.query(Franchisee).all()
    return {f.code: f for f in all_franchisees}


def create_users(db, roles_dict, franchisees_dict):
    """
    创建用户数据
    """
    print("正在创建用户...")
    
    # 检查是否已有数据
    existing_count = db.query(User).count()
    if existing_count > 0:
        print("  用户数据已存在，跳过")
        return
    
    # 密码都是 123456
    default_password = hash_password("123456")
    
    users_data = [
        # 超级管理员
        {
            "username": "admin",
            "password": default_password,
            "real_name": "超级管理员",
            "phone": "13800000001",
            "email": "admin@example.com",
            "role_code": "super_admin",
            "franchisee_code": None,
            "is_superuser": True
        },
        # 运营经理
        {
            "username": "operator",
            "password": default_password,
            "real_name": "张运营",
            "phone": "13800000002",
            "email": "operator@example.com",
            "role_code": "operator",
            "franchisee_code": None,
            "is_superuser": False
        },
        # 运维人员
        {
            "username": "maintainer",
            "password": default_password,
            "real_name": "李运维",
            "phone": "13800000003",
            "email": "maintainer@example.com",
            "role_code": "maintainer",
            "franchisee_code": None,
            "is_superuser": False
        },
        # 财务人员
        {
            "username": "finance",
            "password": default_password,
            "real_name": "王财务",
            "phone": "13800000004",
            "email": "finance@example.com",
            "role_code": "finance",
            "franchisee_code": None,
            "is_superuser": False
        },
        # 加盟商管理员
        {
            "username": "franchisee",
            "password": default_password,
            "real_name": "赵加盟",
            "phone": "13800000005",
            "email": "franchisee@example.com",
            "role_code": "franchisee_admin",
            "franchisee_code": "FRANCHISEE_001",
            "is_superuser": False
        },
        # 二级加盟商管理员
        {
            "username": "shanghai",
            "password": default_password,
            "real_name": "上海管理员",
            "phone": "13800000011",
            "email": "shanghai@example.com",
            "role_code": "franchisee_admin",
            "franchisee_code": "FRANCHISEE_001_01",
            "is_superuser": False
        },
    ]
    
    for u_data in users_data:
        role_id = roles_dict[u_data["role_code"]].id if u_data["role_code"] in roles_dict else None
        franchisee_id = franchisees_dict[u_data["franchisee_code"]].id if u_data["franchisee_code"] in franchisees_dict else None
        
        user = User(
            username=u_data["username"],
            password=u_data["password"],
            real_name=u_data["real_name"],
            phone=u_data["phone"],
            email=u_data["email"],
            role_id=role_id,
            franchisee_id=franchisee_id,
            is_superuser=u_data["is_superuser"],
            is_active=True
        )
        db.add(user)
    
    db.commit()
    print(f"  已创建 {len(users_data)} 个用户")
    print("  默认密码: 123456")
    print("  测试账号:")
    print("    - admin (超级管理员)")
    print("    - operator (运营经理)")
    print("    - maintainer (运维人员)")
    print("    - finance (财务人员)")
    print("    - franchisee (加盟商)")


def create_system_configs(db):
    """
    创建系统配置数据
    """
    print("正在创建系统配置...")
    
    # 检查是否已有数据
    existing_count = db.query(SystemConfig).count()
    if existing_count > 0:
        print("  系统配置已存在，跳过")
        return
    
    configs_data = [
        # 系统参数
        {"category": "system", "key": "system.name", "value": "自动售货机管理系统", "description": "系统名称", "is_public": True},
        {"category": "system", "key": "system.version", "value": "1.0.0", "description": "系统版本", "is_public": True},
        {"category": "system", "key": "system.copyright", "value": "© 2024 Vending System", "description": "版权信息", "is_public": True},
        
        # 支付配置（示例）
        {"category": "payment", "key": "payment.alipay.enabled", "value": "true", "description": "支付宝支付是否启用", "is_public": False},
        {"category": "payment", "key": "payment.wechat.enabled", "value": "true", "description": "微信支付是否启用", "is_public": False},
        {"category": "payment", "key": "payment.cash.enabled", "value": "false", "description": "现金支付是否启用", "is_public": False},
        
        # 短信配置（示例）
        {"category": "sms", "key": "sms.provider", "value": "aliyun", "description": "短信服务商", "is_public": False},
        {"category": "sms", "key": "sms.enabled", "value": "false", "description": "短信服务是否启用", "is_public": False},
        
        # 邮件配置（示例）
        {"category": "email", "key": "email.smtp.host", "value": "smtp.example.com", "description": "SMTP服务器地址", "is_public": False},
        {"category": "email", "key": "email.enabled", "value": "false", "description": "邮件服务是否启用", "is_public": False},
        
        # 显示配置
        {"category": "display", "key": "display.dashboard.refresh_interval", "value": "30", "description": "大屏刷新间隔(秒)", "is_public": True},
        {"category": "display", "key": "display.order.show_count", "value": "20", "description": "实时订单显示数量", "is_public": True},
    ]
    
    for c_data in configs_data:
        config = SystemConfig(
            category=c_data["category"],
            key=c_data["key"],
            value=c_data["value"],
            description=c_data["description"],
            is_public=c_data["is_public"]
        )
        db.add(config)
    
    db.commit()
    print(f"  已创建 {len(configs_data)} 个系统配置")


def create_devices_and_transactions(db, franchisees_dict):
    """
    创建设备和交易测试数据
    """
    print("正在创建设备和交易测试数据...")
    
    # 检查是否已有数据
    existing_device_count = db.query(Device).count()
    if existing_device_count > 0:
        print("  设备数据已存在，跳过")
        return
    
    # 创建设备
    franchisee_list = list(franchisees_dict.values())
    device_statuses = ["online", "online", "online", "online", "offline", "fault"]  # 权重分布
    
    devices = []
    for i in range(1, 51):  # 创建50台设备
        franchisee = random.choice(franchisee_list) if franchisee_list else None
        
        device = Device(
            device_no=f"DEV{str(i).zfill(5)}",
            name=f"自动售货机{i}号",
            model=random.choice(["VM-100", "VM-200", "VM-300", "VM-500"]),
            franchisee_id=franchisee.id if franchisee else None,
            location=f"测试地点{i}号",
            status=random.choice(device_statuses),
            last_online_at=datetime.now() - timedelta(hours=random.randint(0, 24)),
            description=f"测试设备{i}号"
        )
        db.add(device)
        db.flush()
        devices.append(device)
    
    db.commit()
    print(f"  已创建 {len(devices)} 台设备")
    
    # 创建交易数据
    print("正在创建交易测试数据...")
    pay_types = ["wechat", "alipay", "wechat", "wechat", "alipay"]
    statuses = ["success", "success", "success", "success", "failed", "refunded"]
    
    transactions_count = 0
    now = datetime.now()
    
    # 生成最近30天的交易数据
    for day_offset in range(30):
        day = now - timedelta(days=day_offset)
        
        # 每天随机生成若干笔交易
        day_transactions = random.randint(10, 50)
        
        for _ in range(day_transactions):
            device = random.choice(devices)
            
            # 随机时间（当天内）
            hour = random.randint(8, 22)
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            trans_time = day.replace(hour=hour, minute=minute, second=second)
            
            amount = Decimal(str(random.randint(3, 50))) + Decimal(str(random.random())).quantize(Decimal('0.01'))
            
            status = random.choice(statuses)
            pay_time = trans_time + timedelta(seconds=random.randint(5, 30)) if status == "success" else None
            
            transaction = Transaction(
                order_no=f"ORD{day_offset:02d}{trans_time.hour:02d}{trans_time.minute:02d}{random.randint(1000, 9999)}",
                device_id=device.id,
                total_amount=amount,
                pay_amount=amount if status == "success" else Decimal("0"),
                pay_type=random.choice(pay_types),
                status=status,
                pay_time=pay_time,
                created_at=trans_time
            )
            db.add(transaction)
            transactions_count += 1
    
    db.commit()
    print(f"  已创建 {transactions_count} 笔交易")


def main():
    """
    主函数
    """
    print("=" * 60)
    print("  自动售货机管理系统 - 数据库初始化脚本")
    print("=" * 60)
    print()
    
    # 初始化数据库表
    print("正在初始化数据库表...")
    init_db()
    print("  数据库表初始化完成")
    print()
    
    # 创建Session
    db = SessionLocal()
    
    try:
        # 创建权限
        permissions_dict = create_permissions(db)
        print()
        
        # 创建角色
        roles_dict = create_roles(db, permissions_dict)
        print()
        
        # 创建加盟商
        franchisees_dict = create_franchisees(db)
        print()
        
        # 创建用户
        create_users(db, roles_dict, franchisees_dict)
        print()
        
        # 创建系统配置
        create_system_configs(db)
        print()
        
        # 创建设备和交易数据
        create_devices_and_transactions(db, franchisees_dict)
        print()
        
        print("=" * 60)
        print("  数据库初始化完成！")
        print("=" * 60)
        print()
        print("  测试账号（密码均为 123456）:")
        print("    - admin     - 超级管理员")
        print("    - operator  - 运营经理")
        print("    - maintainer- 运维人员")
        print("    - finance   - 财务人员")
        print("    - franchisee- 加盟商管理员")
        print()
        print("  启动命令: python main.py 或 uvicorn main:app --reload --host 0.0.0.0 --port 8000")
        print("  访问地址: http://localhost:8000")
        print()
        
    except Exception as e:
        print(f"初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
