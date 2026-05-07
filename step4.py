import os
import json
from collections import defaultdict

# ==========================================
# 1. 图论算法：跨文档同义词自动融合 (Reduce阶段)
# ==========================================
def build_global_ontology(ontology_dir):
    """
    读取所有局部同义词字典，使用无向图连通分量算法提取全局唯一概念
    """
    graph = defaultdict(set)
    
    # 遍历所有的局部字典文件
    for filename in os.listdir(ontology_dir):
        if filename.endswith(".json"):
            file_path = os.path.join(ontology_dir, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    local_ont = json.load(f)
                except json.JSONDecodeError:
                    continue
                
            for key, synonyms in local_ont.items():
                # 让 Key 和它所有的 Synonym 在图中互相连通
                for syn in synonyms:
                    graph[key].add(syn)
                    graph[syn].add(key)

    visited = set()
    global_ontology = {}
    
    # 寻找所有的连通分量（家族）
    for node in graph:
        if node not in visited:
            queue = [node]
            family_cluster = set()
            
            # BFS 遍历整个家族
            while queue:
                curr = queue.pop(0)
                if curr not in visited:
                    visited.add(curr)
                    family_cluster.add(curr)
                    queue.extend(list(graph[curr] - visited))
                    
            # 选举标准名：在医学文本中，简单地将最长的词作为标准全称
            standard_name = max(family_cluster, key=len)
            concept_id = f"Concept_{standard_name}"
            global_ontology[concept_id] = list(family_cluster)

    return global_ontology

# ==========================================
# 2. 规则洗刷与对齐 (剥离了微调打包逻辑)
# ==========================================
def align_dataset(rules_dir, global_ontology, output_file):
    """
    利用全局本体对齐生肉规则，输出纯净的图式规则 JSON 数组
    """
    # 构建极速反向查找表 (O(1) 复杂度): {"IAI": "Concept_腹腔内感染"}
    reverse_lookup = {}
    for concept_id, synonyms in global_ontology.items():
        for syn in synonyms:
            reverse_lookup[syn] = concept_id

    all_aligned_rules = []
    total_aligned_rules = 0

    # 遍历经过 Step 2.5 清洗的生肉规则文件
    for filename in os.listdir(rules_dir):
        if filename.endswith(".json"):
            file_path = os.path.join(rules_dir, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    rules = json.load(f)
                except json.JSONDecodeError:
                    continue
            
            # 兼容旧格式（直接是列表）或带头部的格式
            rules_list = rules.get("rules", []) if isinstance(rules, dict) else rules

            for rule in rules_list:
                # --- 核心操作：同义词替换 (实体对齐) ---
                if "head" in rule and "arguments" in rule["head"]:
                    rule["head"]["arguments"] = [
                        reverse_lookup.get(arg, arg) for arg in rule["head"]["arguments"]
                    ]
                
                if "body" in rule:
                    for predicate in rule["body"]:
                        if "arguments" in predicate:
                            predicate["arguments"] = [
                                reverse_lookup.get(arg, arg) for arg in predicate["arguments"]
                            ]
                # --------------------------------------
                
                # 直接保留原始字典结构（包含 source_text），追加到总列表
                all_aligned_rules.append(rule)
                total_aligned_rules += 1

    # 写入最终的纯血 AST JSON 文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_aligned_rules, f, ensure_ascii=False, indent=2)

    return total_aligned_rules

# ==========================================
# 3. 主程序调度
# ==========================================
def main():
    ontology_dir = "output_ontology"      # Step 3 生成的目录
    rules_dir = "output_json_cleaned"     # 【关键更改】指向 Step 2.5 清洗后的目录
    
    print("==================================================")
    print("🚀 启动 Step 4: 全局本体融合与图式规则对齐")
    print("==================================================")
    
    if not os.path.exists(ontology_dir) or not os.path.exists(rules_dir):
        print(f"❌ 找不到必要的文件夹，请确保 {ontology_dir} 和 {rules_dir} 均已存在。")
        return

    # 任务 1：图论合并
    print("1️⃣ 正在执行跨文档同义词融合 (Graph Connected Components)...")
    global_ontology = build_global_ontology(ontology_dir)
    
    with open("GLOBAL_ONTOLOGY.json", 'w', encoding='utf-8') as f:
        json.dump(global_ontology, f, ensure_ascii=False, indent=2)
    print(f"   ✅ 成功构建全局本体大字典！共提取 {len(global_ontology)} 个核心医学概念家族。")
    print(f"   💾 已保存至: GLOBAL_ONTOLOGY.json")
    
    # 任务 2：规则纯粹对齐
    print("\n2️⃣ 正在使用全局字典对生肉规则进行强对齐...")
    final_output = "aligned_rules_zh.json"
    total_rules = align_dataset(rules_dir, global_ontology, final_output)
    
    print(f"   ✅ 成功对齐了 {total_rules} 条图式规则。")
    print(f"   💾 纯血对齐版 AST 数据集已保存至: {final_output}")
    print("==================================================")

if __name__ == "__main__":
    main()