import json
import os

def count_schema_rules(file_path):
    print("==================================================")
    print(f"📊 启动规则统计器: 正在分析 {os.path.basename(file_path)}")
    print("==================================================")
    
    if not os.path.exists(file_path):
        print(f"❌ 找不到文件: {file_path}")
        return 0

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # 兼容处理：检查数据结构
        if isinstance(data, list):
            # 格式 1：纯血 AST JSON 数组 (如 aligned_rules_zh.json)
            rule_count = len(data)
        elif isinstance(data, dict) and "rules" in data:
            # 格式 2：带有包裹层的 JSON (如部分生肉数据)
            rule_count = len(data["rules"])
        else:
            print("⚠️ 无法识别的 JSON 结构，期望是一个规则列表或包含 'rules' 键的字典。")
            return 0
            
        print(f"   ✅ 统计完成！该文件共包含 【 {rule_count} 】 条图式规则。")
        print("==================================================")
        return rule_count
        
    except json.JSONDecodeError:
        print(f"❌ JSON 解析失败，请检查文件 {file_path} 的格式是否正确。")
        return 0
    except Exception as e:
        print(f"❌ 读取文件时发生未知错误: {e}")
        return 0

if __name__ == "__main__":
    # 你可以随时在这里修改你要统计的文件名
    # 比如 "ultimate_rules__【医脉通】中国腹腔感染诊治指南（2019版）1-8页.json" 
    # 或者 "aligned_rules_zh.json"
    target_file = "aligned_rules_zh_cleaned.json" 
    
    count_schema_rules(target_file)