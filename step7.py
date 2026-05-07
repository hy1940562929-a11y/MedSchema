import os
import json

def convert_to_jsonld(input_file, output_file):
    print("==================================================")
    print("🌐 启动 Step 7: ISWC 语义网 JSON-LD 升维引擎")
    print("==================================================")
    
    if not os.path.exists(input_file):
        print(f"❌ 找不到输入文件 {input_file}，请确保纯净版 AST 数据已生成。")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        aligned_rules = json.load(f)

    # 1. 定义极其关键的 JSON-LD 上下文 (@context)
    # 这就是向 ISWC 评委证明你懂 Semantic Web 的核心
    jsonld_context = {
        # 定义我们数据集的专属命名空间
        "medschema": "http://example.org/medschema/ontology#",
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        
        # 映射 JSON 的键名到本体属性
        "Rule": "medschema:SchemaRule",
        "Predicate": "medschema:LogicalPredicate",
        "rule_name": "rdfs:label",
        "source_text": "rdfs:comment",
        "has_head": {"@id": "medschema:hasHead", "@type": "@id"},
        "has_body": {"@id": "medschema:hasBody", "@type": "@id"},
        "is_negative": "medschema:isNegative",
        "predicate_name": "medschema:predicateName",
        
        # 将论元定义为有序列表 (@list)
        "arguments": {"@id": "medschema:hasArgument", "@container": "@list"}
    }

    # 2. 构建知识图谱的图节点 (@graph)
    graph_nodes = []
    
    def process_predicate(pred_dict, pred_id):
        """将普通的字典谓词转化为 JSON-LD 节点"""
        # 处理论元：如果是 Concept_ 开头，转化为标准的 URI
        processed_args = []
        for arg in pred_dict.get("arguments", []):
            if arg.startswith("Concept_"):
                processed_args.append(f"medschema:{arg}")
            else:
                # 变量(如 X, Y)或普通常量作为普通字符串保留
                processed_args.append(arg)
                
        return {
            "@id": pred_id,
            "@type": "Predicate",
            "predicate_name": pred_dict.get("name", ""),
            "is_negative": pred_dict.get("is_negative", False),
            "arguments": processed_args
        }

    for idx, rule in enumerate(aligned_rules):
        rule_id = f"medschema:Rule_{idx+1:04d}"
        
        # 处理 Head
        head_node = None
        if "head" in rule:
            head_id = f"{rule_id}_Head"
            head_node = process_predicate(rule["head"], head_id)
            
        # 处理 Body
        body_nodes = []
        if "body" in rule:
            for b_idx, b_pred in enumerate(rule["body"]):
                b_id = f"{rule_id}_Body_{b_idx+1}"
                body_nodes.append(process_predicate(b_pred, b_id))

        # 组装当前 Rule 节点
        rule_node = {
            "@id": rule_id,
            "@type": "Rule",
            "rule_name": rule.get("rule_name", f"Rule {idx+1}"),
            "source_text": rule.get("source_text", ""),
        }
        
        if head_node:
            rule_node["has_head"] = head_node
        if body_nodes:
            rule_node["has_body"] = body_nodes

        graph_nodes.append(rule_node)

    # 3. 组装最终的 JSON-LD 文档
    jsonld_document = {
        "@context": jsonld_context,
        "@graph": graph_nodes
    }

    # 4. 写入文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(jsonld_document, f, ensure_ascii=False, indent=2)

    print(f"   ✅ 成功将 {len(aligned_rules)} 条普通 JSON 规则转化为 Linked Data。")
    print(f"   💾 JSON-LD 知识图谱已保存至: {output_file}")
    print("==================================================")

if __name__ == "__main__":
    convert_to_jsonld("aligned_rules_zh.json", "MedSchema_knowledge_graph.jsonld")