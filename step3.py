import os
import json
import re
from openai import OpenAI
import concurrent.futures

# ==========================================
# 1. DeepSeek API configuration
# ==========================================
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

if not DEEPSEEK_API_KEY:
    raise RuntimeError("Please set the DEEPSEEK_API_KEY environment variable before running step3.py.")

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_BASE_URL
)

# ==========================================
# 2. 极度严格的同义词提取 Prompt
# ==========================================
STRICT_ONTOLOGY_PROMPT = """
你是一位极其严谨的医学知识图谱本体架构师。
我将给你提供一段医学指南的【原始长篇章】。你的唯一任务是：提取该文本中明确出现的**完全等价的医学同义词**。

# 🚨 【极度严格的聚类标准】(违背任何一条将导致系统崩溃)
1. **绝对等价原则**：只能将**指代完全相同事物的词汇**聚类。例如，中文全称与英文缩写（如“急性胃肠功能损伤”与“AGI”、“腹腔内感染”与“IAI”），或者极其明显的临床同义称呼。
2. **禁止上下位词混合**：绝对不允许把包含、从属关系的词混为一谈！例如，“抗生素”和“替加环素”绝不是同义词；“IAI”和“重度IAI”绝不是同义词（后者是前者的一个子集）！
3. **只认原文**：只提取在提供的文本中**真实出现过**的词，绝不允许凭借你的知识去捏造文本中没有出现的同义词。
4. **剔除日常词汇**：不要提取“病人”和“患者”、“提高”和“增加”这类没有医学专业价值的普通词汇。只针对疾病、药物、临床指标、生理状态等核心医学实体！

# 强制 JSON 输出格式
你必须返回一个合法的 JSON 对象。键（Key）是你推导出的【标准医学名词】，值（Value）是该段文本中出现的【所有等价同义词组成的列表】（包含Key本身如果在原文中出现的话）。
如果没有发现任何符合严格标准的同义词，请返回空的 JSON 对象：{}

示例格式：
{
  "急性胃肠功能损伤": ["急性胃肠功能损伤", "AGI"],
  "多重耐药菌": ["多重耐药菌", "MDR"]
}
"""

# ==========================================
# 3. 核心解析与合并函数
# ==========================================
def extract_source_texts(file_path):
    """用正则表达式从 txt 文件中精准扒出所有的【原始长篇章】"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 匹配【原始长篇章】: 和 【规则 1】 之间的文本
    pattern = r"【原始长篇章】:(.*?)(?=\n【规则 1】|### 来自文本块|$)"
    source_texts = re.findall(pattern, content, re.DOTALL)
    
    # 清洗掉多余的空格和换行
    return [text.strip() for text in source_texts if text.strip()]

def extract_ontology_from_text(text_chunk, index):
    """调用 V3 模型进行极度严格的同义词提取"""
    try:
        response = client.chat.completions.create(
            model="deepseek-chat", # 提取同义词使用 V3，速度快且 JSON 能力强
            messages=[
                {"role": "system", "content": STRICT_ONTOLOGY_PROMPT},
                {"role": "user", "content": f"请提取以下文本的同义词：\n\n{text_chunk}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.0 # 温度设为绝对的0，剥夺大模型的创造力，强制其严格遵守文本
        )
        result = json.loads(response.choices[0].message.content)
        if result:
            print(f"  ✅ 文本段 {index} 同义词提取成功: 发现 {len(result)} 组实体。")
        else:
            print(f"  ⏭️ 文本段 {index} 未发现符合严格标准的同义词，跳过。")
        return result
    except Exception as e:
        print(f"  ❌ 文本段 {index} 提取失败: {e}")
        return {}

# ==========================================
# 4. 主程序
# ==========================================
def main():
    input_dir = "output_rules"
    output_dir = "output_ontology"
    if not os.path.exists(output_dir): os.makedirs(output_dir)

    for filename in os.listdir(input_dir):
        if filename.startswith("ultimate_rules_") and filename.endswith(".txt"):
            print(f"\n🚀 开始提取文档级严格本体字典: {filename}")
            
            # 1. 精准提取原始文本
            source_texts = extract_source_texts(os.path.join(input_dir, filename))
            print(f"✂️ 共识别出 {len(source_texts)} 段复杂原始文本。")
            
            document_ontology = {}
            
            # 2. 多线程并发请求大模型找同义词
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                future_to_index = {executor.submit(extract_ontology_from_text, text, i+1): i for i, text in enumerate(source_texts)}
                
                for future in concurrent.futures.as_completed(future_to_index):
                    local_dict = future.result()
                    # 3. 将各个文本段的字典融合为单篇文档的总字典
                    if local_dict:
                        for std_key, syn_list in local_dict.items():
                            if std_key not in document_ontology:
                                document_ontology[std_key] = []
                            # 合并列表并去重
                            document_ontology[std_key] = list(set(document_ontology[std_key] + syn_list))

            # 4. 一对一输出保存
            output_file = os.path.join(output_dir, f"{filename.replace('ultimate_rules_', 'ontology_').replace('.txt', '.json')}")
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(document_ontology, f, ensure_ascii=False, indent=2)
                
            print(f"🎉 提取完成！单文档本体字典已保存至: {output_file}")
            print(f"📊 本篇文档共严格提取出 {len(document_ontology)} 个核心医学概念及其同义词。")

if __name__ == "__main__":
    main()
