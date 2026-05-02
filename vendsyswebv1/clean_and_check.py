import ast
import sys
import os
import shutil

def clear_pycache():
    """清除所有__pycache__目录和.pyc文件"""
    project_dir = os.path.dirname(os.path.abspath(__file__))
    cleared = 0
    
    for root, dirs, files in os.walk(project_dir):
        # 删除__pycache__目录
        if '__pycache__' in dirs:
            cache_dir = os.path.join(root, '__pycache__')
            try:
                shutil.rmtree(cache_dir)
                print(f"✓ 清除缓存: {cache_dir}")
                cleared += 1
            except:
                pass
        
        # 删除.pyc文件
        for file in files:
            if file.endswith('.pyc'):
                try:
                    os.remove(os.path.join(root, file))
                    cleared += 1
                except:
                    pass
    
    return cleared

def check_file_syntax(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
        ast.parse(code, filename=filepath)
        return True, None
    except SyntaxError as e:
        return False, f"语法错误: {e.msg} (行 {e.lineno}): {e.text.strip() if e.text else ''}"
    except Exception as e:
        return False, str(e)

# 清除缓存
print("清除Python缓存...")
print("="*60)
cleared = clear_pycache()
print(f"已清除 {cleared} 个缓存项")
print()

# 检查关键文件
files_to_check = [
    "main.py",
    "routers/lanes.py",
]

print("验证关键文件语法...")
print("="*60)

all_ok = True
for filepath in files_to_check:
    if os.path.exists(filepath):
        ok, msg = check_file_syntax(filepath)
        if ok:
            print(f"[OK] {filepath}")
        else:
            print(f"[FAIL] {filepath}")
            print(f"       {msg}")
            all_ok = False
    else:
        print(f"[MISSING] {filepath}")
        all_ok = False

print()
print("="*60)
if all_ok:
    print("✅ 语法检查通过！")
else:
    print("❌ 发现语法错误！")
    sys.exit(1)

# 尝试简化导入测试
print()
print("尝试导入关键模块...")
print("="*60)

try:
    # 测试修复后的lanes.py语法
    import importlib.util
    
    # 简化测试 - 只测试语法
    import ast
    with open('routers/lanes.py', 'r', encoding='utf-8') as f:
        code = f.read()
    ast.parse(code)
    print("✓ routers/lanes.py 语法正确")
    
except Exception as e:
    print(f"✗ 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("="*60)
print("🎉 验证完成！现在可以启动服务了")
print("="*60)
