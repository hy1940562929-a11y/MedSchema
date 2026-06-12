import os
import json
import re
from pydantic import BaseModel, Field
from typing import List, Dict
from openai import OpenAI
import concurrent.futures

# ==========================================
# 1. DeepSeek API configuration
# ==========================================
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

if not DEEPSEEK_API_KEY:
    raise RuntimeError("Please set the DEEPSEEK_API_KEY environment variable before running step2.py.")

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_BASE_URL
)

# ==========================================
# 2. 定义严谨的 Pydantic 数据结构 (AST语法树)
# ==========================================
class Predicate(BaseModel):
    is_negative: bool = Field(description="是否包含否定符号(如¬或'不')")
    name: str = Field(description="谓词名称，例如'患有', '用药推荐', '属于'")
    arguments: List[str] = Field(description="谓词的论元列表，长度必须 <= 3。例如 ['X', '胺碘酮', '强烈推荐']")

class SchemaRule(BaseModel):
    rule_name: str = Field(description="规则的简短名称")
    head: Predicate = Field(description="规则头（结论）。注意：必须是原子的，只能有一个谓词！")
    body: List[Predicate] = Field(description="规则体（前提条件）。包含多个谓词的合取(AND)。")
    variables: Dict[str, str] = Field(description="变量字典，例如 {'X': '患者', 'Y': '疾病'}")
    source_text: str = Field(description="这条规则对应的原始指南长篇章文本")

class RuleSet(BaseModel):
    rules: List[SchemaRule] = Field(description="提取出的一组图式规则")

# 获取 JSON Schema 字符串，用于喂给大模型
RULE_SCHEMA_JSON = RuleSet.model_json_schema()

# ==========================================
# 3. 结构化解析 Prompt
# ==========================================
JSON_PARSER_PROMPT = f"""
你是一个精密的编译器。你的任务是将传入的【纯文本图式规则】解析为严格的 JSON 抽象语法树（AST）。

# 解析规则与自动纠偏机制：
1. **原子化规则头（Atomic Head）**：如果输入的文本中，规则头（<- 左侧）包含多个谓词（出现了 ^ 或 AND），你必须自行决定一个最核心的结论作为 `head`，将其余的条件移入 `body` 中。`head` 绝对只能是一个谓词。
2. **过滤静态事实**：如果发现某条规则完全没有使用变量（如 X, Y），全部是常量（如 `推荐等级(APACHE, 优先)`），这属于静态事实，请直接【丢弃】这条规则，不要放入最终的 JSON 列表中。
3. **元数约束**：拆解 `arguments` 时，列表长度绝对不能超过 3！
4. **否定提取**：如果谓词前有 `¬`，将 `is_negative` 设为 true，并把 `¬` 从 `name` 中去掉。
5. 纯粹事实过滤禁令：你必须剔除所有属于“统计学指标、文献分析、证据等级”的废话！如果遇到“Meta分析结论”、“证据质量”、“灵敏度”、“特异度”、“AUC”等谓词，直接将其从 body 中彻底删除。规则体只能保留患者的临床病理事实或干预动作！
# JSON Schema 约束：
你必须且只能返回符合以下 JSON Schema 的结构：
{json.dumps(RULE_SCHEMA_JSON, ensure_ascii=False)}

请直接输出 JSON，不要有任何 Markdown 标记或多余的解释！
"""

# ==========================================
# 4. 辅助与核心解析函数
# ==========================================
def parse_text_to_blocks(file_path):
    """将 Step 1 生成的 txt 文件按 '---' 分割为文本块"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 按照之前设定的 --- 分割符切分
    blocks = re.split(r'\n---\n', content)
    return [b.strip() for b in blocks if b.strip()]

def convert_block_to_json(block_text, index):
    """调用 DeepSeek-V3 进行 JSON 结构化转换"""
    try:
        response = client.chat.completions.create(
            model="deepseek-chat", # 这里使用 V3 模型，速度极快且 JSON 遵循能力完美
            messages=[
                {"role": "system", "content": JSON_PARSER_PROMPT},
                {"role": "user", "content": f"请解析以下文本块：\n\n{block_text}"}
            ],
            response_format={"type": "json_object"}, # 强制 JSON 输出模式
            temperature=0.1
        )
        result = response.choices[0].message.content
        print(f"  ✅ 文本块 {index} JSON化完成！")
        return json.loads(result)
    except Exception as e:
        print(f"  ❌ 文本块 {index} JSON化失败: {e}")
        return None

# ==========================================
# 5. 主程序
# ==========================================
def main():
    input_dir = "output_rules"
    output_dir = "output_json"
    if not os.path.exists(output_dir): os.makedirs(output_dir)

    for filename in os.listdir(input_dir):
        if filename.startswith("ultimate_rules_") and filename.endswith(".txt"):
            print(f"\n🚀 开始结构化文档: {filename}")
            file_path = os.path.join(input_dir, filename)
            
            # 1. 拆分文本块
            blocks = parse_text_to_blocks(file_path)
            print(f"✂️ 共发现 {len(blocks)} 个规则块，启动并发转换...")
            
            all_json_rules = []
            
            # 2. 多线程调用 V3
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                future_to_index = {executor.submit(convert_block_to_json, block, i+1): i for i, block in enumerate(blocks)}
                
                for future in concurrent.futures.as_completed(future_to_index):
                    res = future.result()
                    if res and "rules" in res:
                        all_json_rules.extend(res["rules"]) # 将所有规则合并到一个大列表中

            # 3. 保存最终的 JSON 数据集
            if all_json_rules:
                output_file = os.path.join(output_dir, f"{filename.replace('.txt', '.json')}")
                with open(output_file, "w", encoding="utf-8") as f:
                    # 格式化保存 JSON，方便人工核对
                    json.dump(all_json_rules, f, ensure_ascii=False, indent=2)
                print(f"🎉 结构化完成！JSON 语料库已保存至: {output_file}")
                print(f"📊 本次共提纯出 {len(all_json_rules)} 条标准图式规则。")

if __name__ == "__main__":
    main()
