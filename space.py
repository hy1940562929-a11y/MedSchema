import os
import json

def fix_concept_spaces(file_path):
    print("==================================================")
    print("🔧 启动热修复: 洗刷 Concept ID 中的非法空格")
    print("==================================================")
    
    if not os.path.exists(file_path):
        print(f"❌ 找不到文件: {file_path}")
        return

    # 1. 读取当前的 AST JSON 数据
    with open(file_path, 'r', encoding='utf-8') as f:
        aligned_rules = json.load(f)

    space_fixed_count = 0

    # 内部函数：专门处理论元列表
    def process_arguments(args):
        nonlocal space_fixed_count
        new_args = []
        for arg in args:
            # 只有当它是字符串、以 Concept_ 开头，且包含空格时，才进行替换
            if isinstance(arg, str) and arg.startswith("Concept_") and " " in arg:
                fixed_arg = arg.replace(" ", "_")
                new_args.append(fixed_arg)
                space_fixed_count += 1
            else:
                new_args.append(arg)
        return new_args

    # 2. O(N) 复杂度遍历整棵语法树
    for rule in aligned_rules:
        # 扫描并修复 Head 中的论元
        if "head" in rule and "arguments" in rule["head"]:
            rule["head"]["arguments"] = process_arguments(rule["head"]["arguments"])
            
        # 扫描并修复 Body 中的论元
        if "body" in rule:
            for predicate in rule["body"]:
                if "arguments" in predicate:
                    predicate["arguments"] = process_arguments(predicate["arguments"])

    # 3. 将修复后的数据原地覆盖写回
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(aligned_rules, f, ensure_ascii=False, indent=2)

    print(f"   ✅ 扫描完毕！共修复了 {space_fixed_count} 处带有空格的非法 URI 节点。")
    print(f"   💾 数据已原地更新至: {file_path}")
    print("==================================================")

if __name__ == "__main__":
    # 直接对 Step 4 生成的中间件进行洗刷
    target_file = "aligned_rules_zh.json" 
    fix_concept_spaces(target_file)