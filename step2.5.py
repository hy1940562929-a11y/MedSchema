import os
import json
import re

# ==========================================
# 1. 核心清洗引擎：治疗 "PDF解析空格病"
# ==========================================
def clean_source_text(text):
    """
    智能清洗多余空格，保留必要的英文单词间距
    """
    if not text:
        return ""
        
    # 1. 将换行符、制表符及多个连续空格，统一替换为单个空格
    text = re.sub(r'\s+', ' ', text)
    
    # 2. 删除【中文与中文】之间的空格
    text = re.sub(r'(?<=[\u4e00-\u9fa5])\s+(?=[\u4e00-\u9fa5])', '', text)
    
    # 3. 删除【中文与英文字母/数字】之间的空格 (例如 "共10 篇" -> "共10篇")
    text = re.sub(r'(?<=[\u4e00-\u9fa5])\s+(?=[a-zA-Z0-9])', '', text)
    text = re.sub(r'(?<=[a-zA-Z0-9])\s+(?=[\u4e00-\u9fa5])', '', text)
    
    # 4. 删除【中文与全角标点符号】之间的空格
    text = re.sub(r'(?<=[\u4e00-\u9fa5])\s+(?=[，。！？（）《》【】、；：])', '', text)
    text = re.sub(r'(?<=[，。！？（）《》【】、；：])\s+(?=[\u4e00-\u9fa5])', '', text)
    
    return text.strip()

# ==========================================
# 2. 主程序：批量清洗
# ==========================================
def main():
    input_dir = "output_json"           # Step 2 的输出目录
    output_dir = "output_json_cleaned"  # Step 2.5 的输出目录（安全隔离，不覆盖原文件）
    
    print("==================================================")
    print("🧹 启动 Step 2.5: 原始文本专用清洗器 (去除 PDF 乱码空格)")
    print("==================================================")

    if not os.path.exists(input_dir):
        print(f"❌ 找不到输入目录: {input_dir}")
        return

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    total_files = 0
    total_rules_cleaned = 0

    for filename in os.listdir(input_dir):
        if filename.endswith(".json"):
            input_file = os.path.join(input_dir, filename)
            output_file = os.path.join(output_dir, filename)
            
            with open(input_file, 'r', encoding='utf-8') as f:
                try:
                    document_data = json.load(f)
                except json.JSONDecodeError:
                    print(f"⚠️ 文件 {filename} 解析失败，跳过。")
                    continue
            
            # 兼容读取规则列表
            rules_list = document_data.get("rules", []) if isinstance(document_data, dict) else document_data
            
            # 遍历并清洗每一条规则的 source_text
            for rule in rules_list:
                if "source_text" in rule:
                    original_text = rule["source_text"]
                    cleaned_text = clean_source_text(original_text)
                    rule["source_text"] = cleaned_text
                    total_rules_cleaned += 1

            # 将洗干净的数据（包含原有的 head 和 body）完整保存到新目录
            final_data = {"rules": rules_list} if isinstance(document_data, dict) and "rules" in document_data else rules_list
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(final_data, f, ensure_ascii=False, indent=2)
            
            total_files += 1
            print(f"  ✅ 已清洗: {filename}")

    print("==================================================")
    print(f"🎉 清洗完成！")
    print(f"📊 统计：处理了 {total_files} 个文件，清洗了 {total_rules_cleaned} 段文本。")
    print(f"💾 纯净版 JSON 已安全隔离并保存至: '{output_dir}/' 文件夹")
    print("==================================================")

if __name__ == "__main__":
    main()