import json
from collections import defaultdict

def calculate_statistics(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    total_rules = len(data)
    unique_entities = set()
    unique_predicates = set()
    arity_counts = defaultdict(int)
    negative_rule_count = 0
    max_premises = 0
    total_premises = 0

    for rule in data:
        has_negative = False
        
        # 1. 统计变量 (Variables)，变量对应的值属于医学实体
        vars_dict = rule.get("variables", {})
        vars_keys = set(vars_dict.keys())
        for val in vars_dict.values():
            unique_entities.add(val)
            
        # 2. 统计前提 (Body)
        body = rule.get("body", [])
        max_premises = max(max_premises, len(body))
        total_premises += len(body)
        
        # 3. 汇总所有的谓词 (Head + Body)
        predicates = [rule.get("head", {})] + body
        
        for pred in predicates:
            if not pred:
                continue
                
            # 统计独立谓词种类
            pred_name = pred.get("name")
            if pred_name:
                unique_predicates.add(pred_name)
                
            # 统计是否包含否定算子
            if pred.get("is_negative"):
                has_negative = True
                
            # 统计元数 (Arity)
            args = pred.get("arguments", [])
            arity = len(args)
            arity_counts[arity] += 1
            
            # 统计生肉论元 (实体) - 排除掉变量占位符(如 X, Y)
            for arg in args:
                if arg not in vars_keys:
                    unique_entities.add(arg)
                    
        # 如果整条规则包含至少一个否定算子
        if has_negative:
            negative_rule_count += 1

    # 打印优美的统计报表
    print("="*40)
    print("🏥 MedSchema 数据集统计报告 (MSR Stats)")
    print("="*40)
    print(f"Total Schema Rules (规则总数): {total_rules:,}")
    print(f"Unique Clinical Entities (独立医学实体数): {len(unique_entities):,}")
    print(f"Unique Predicates (独立谓词数): {len(unique_predicates):,}")
    print(f"Rules with Negative Operators (包含显式否定的规则数): {negative_rule_count:,}")
    print("-" * 40)
    print(f"Max Premises per Rule (单条规则最大前提数): {max_premises}")
    print(f"Avg. Premises per Rule (平均前提数量): {total_premises / total_rules:.2f}")
    print("-" * 40)
    print("谓词元数 (Arity) 分布:")
    for arity in sorted(arity_counts.keys()):
        print(f"  - Arity {arity}: {arity_counts[arity]:,} 个")
    print("="*40)

if __name__ == "__main__":
    calculate_statistics('aligned_rules_zh.json')