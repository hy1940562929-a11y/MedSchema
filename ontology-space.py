import os
import json

def sanitize_ontology_keys(file_path):
    print("==================================================")
    print("🧬 启动根源修复: 洗刷全局大字典中的非法空格")
    print("==================================================")
    
    if not os.path.exists(file_path):
        print(f"❌ 找不到文件: {file_path}")
        return

    # 读取旧字典
    with open(file_path, 'r', encoding='utf-8') as f:
        ontology = json.load(f)

    clean_ontology = {}
    space_fixed_count = 0

    # 遍历字典，清洗键名
    for old_key, synonyms in ontology.items():
        if " " in old_key:
            # 将空格替换为下划线
            new_key = old_key.replace(" ", "_")
            space_fixed_count += 1
        else:
            new_key = old_key
            
        clean_ontology[new_key] = synonyms

    # 将干净的字典覆盖写回
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(clean_ontology, f, ensure_ascii=False, indent=2)

    print(f"   ✅ 根源洗刷完毕！共修复了 {space_fixed_count} 个带有空格的核心概念 ID。")
    print(f"   💾 纯净版字典已原地更新至: {file_path}")
    print("==================================================")

if __name__ == "__main__":
    target_file = "GLOBAL_ONTOLOGY.json" 
    sanitize_ontology_keys(target_file)