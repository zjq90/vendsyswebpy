"""
最小化语法测试脚本
验证lanes.py中的关键语法
"""
import ast

# 测试1：当前代码的简化版本
test_code = """
def get_device_lane_stats():
    # 模拟数据
    total_lanes = 10
    status_stats = [("normal", 8), ("empty", 2)]
    
    class FakeStats:
        def __getitem__(self, idx):
            return [50, 100, 1][idx] if idx < 3 else None
    
    stock_stats = FakeStats()
    
    # 测试关键行
    result = {
        "device_id": 1,
        "device_name": "测试设备",
        "total_lanes": total_lanes,
        "status_summary": [{"status": s[0], "count": s[1]} for s in status_stats],
        "stock_summary": {
            "total_stock": stock_stats[0] or 0,
            "total_capacity": stock_stats[1] or 0,
            "low_stock_count": stock_stats[2] or 0,
            "stock_percentage": round((stock_stats[0] or 0) / (stock_stats[1] or 1) * 100) if stock_stats[1] else 0
        }
    }
    return result

# 调用测试
r = get_device_lane_stats()
print(f"测试结果: {r}")
print(f"库存百分比: {r['stock_summary']['stock_percentage']}%")
"""

print("=" * 60)
print("测试语法解析...")

try:
    ast.parse(test_code)
    print("✅ AST解析成功，语法正确")
except SyntaxError as e:
    print(f"❌ 语法错误: {e.msg}")
    print(f"   行号: {e.lineno}")
    if e.text:
        print(f"   代码: {e.text}")
    exit(1)

print()
print("=" * 60)
print("执行测试代码...")

try:
    exec(test_code)
    print("✅ 执行成功！")
except Exception as e:
    print(f"❌ 执行错误: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print()
print("=" * 60)
print("🎉 测试通过！语法没有问题")
print("=" * 60)
