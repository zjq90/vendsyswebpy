"""
语法检查脚本
用于检查项目中所有Python文件的语法错误
"""
import ast
import sys
from pathlib import Path

project_dir = Path(__file__).parent
py_files = list(project_dir.rglob("*.py"))

print(f"检查 {len(py_files)} 个Python文件...")
print("-" * 60)

has_errors = False

for py_file in sorted(py_files):
    # 跳过__pycache__和虚拟环境
    if "__pycache__" in str(py_file) or ".venv" in str(py_file) or "venv" in str(py_file):
        continue
    
    rel_path = py_file.relative_to(project_dir)
    try:
        with open(py_file, 'r', encoding='utf-8') as f:
            source = f.read()
        # 尝试解析AST来检查语法
        ast.parse(source)
        print(f"✓ {rel_path}")
    except SyntaxError as e:
        has_errors = True
        print(f"✗ {rel_path}")
        print(f"  错误: {e.msg}")
        print(f"  行号: {e.lineno}")
        if e.text:
            print(f"  代码: {e.text.strip()}")
        print("-" * 60)
    except Exception as e:
        print(f"? {rel_path} - 读取失败: {e}")

print("-" * 60)
if has_errors:
    print("❌ 发现语法错误！")
    sys.exit(1)
else:
    print("✅ 所有Python文件语法检查通过！")
    sys.exit(0)
