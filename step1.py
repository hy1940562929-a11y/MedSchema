import os
import time
import fitz  # PyMuPDF
from openai import OpenAI
import concurrent.futures

# ==========================================
# 1. DeepSeek API configuration
# ==========================================
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

if not DEEPSEEK_API_KEY:
    raise RuntimeError("Please set the DEEPSEEK_API_KEY environment variable before running step1.py.")

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_BASE_URL
)

# ==========================================
# 2. 极压指令 (ISWC级单点爆破)
# ==========================================
SNIPER_PROMPT_TEMPLATE = """
# 角色与任务
你是一位严谨的符号逻辑专家。你的任务是根据给定的【文本切片】，严格按照特定的“图式规则（Schema Rules）”范式，进行文档级一阶逻辑规则提取。

# 理论基础：图式规则的严格形式化定义
图式规则用以表达非线性的复杂因果关系。其必须严格遵循以下巴科斯范式（BNF）底层结构：
1. 【元数绝对限制】：谓词最高只能是三元！
   - 一元谓词 c(X)：仅用于表示实体类型或状态属性（例如：`糖尿病患者(X)`、`重度(X)`）对于规则体出现的实体变量，必须先用一阶谓词声明。
   - 二元谓词 r(X, Y)：用于表示实体间的核心图状关系（例如：`所属患者(Y, X)`、`并发疾病(X, 脓毒症)`）。
   - 三元谓词 r(X, Y, a)：仅限于用第三个参数（常量）修饰二元关系（例如：`后遗症(关节内骨折, 创伤性关节炎, 最常见)`、`用药推荐(X, 胺碘酮, 强烈首选)`）。绝对禁止出现四元及以上的谓词！
2. 【禁止嵌套与集合】：谓词的论元（参数）只能是变量（X, Y, Z）或单一常量。绝对禁止在谓词内部嵌套谓词（如 r1(r2(X))）或使用集合（如 {{a, b}}）。
3. 【图状拓扑】：规则体（<- 右侧）的变量引用必须呈现“非线性因果”的网络结构（例如 X 关联 Y，且 X 关联 Z，Y 关联 W），不能是简单的单线链式推导。
4. 【精准否定】：对于排他性或未发生的前提，必须使用否定符号（如 `¬过敏史(X, 青霉素)`）。

# 【绝对禁令】：彻底封杀“V (或者)”与括号嵌套！
- 你的逻辑表达中**绝对不允许出现 `V`、`∨`、`OR` 或任何表示“或者”的逻辑符号！**
- 如果原文中出现“满足A或B均可”的并列条件，你**必须**将其拆分为两条独立、平行的规则。
- 逻辑表达的 <- 右侧，只能使用 `^`（AND）进行连接，且绝对不准使用圆括号 `()` 进行逻辑分块。

# 优秀少样本参考 (Few-Shot Examples)

【样例 1：演示彻底拆分“V(或者)”与精准否定】
原文："对于骨质疏松的绝经后妇女，如果之前发生过脆性骨折或T值低于-2.5，强烈建议使用特立帕肽，但若有骨肉瘤病史则绝对禁用。"
正确输出：
【规则 1】
规则名: 绝经后妇女特立帕肽强烈推荐指征_脆性骨折
逻辑表达: 用药推荐(X, 特立帕肽, 强烈) <- 绝经后妇女(X) ^ 患病(X, 骨质疏松) ^ 既往病史(X, 脆性骨折) ^ ¬既往病史(X, 骨肉瘤)
变量映射: 
  - X: 患者

【规则 2】
规则名: 绝经后妇女特立帕肽强烈推荐指征_T值达标
逻辑表达: 用药推荐(X, 特立帕肽, 强烈) <- 绝经后妇女(X) ^ 患病(X, 骨质疏松) ^ 骨密度指标(X, T值低于-2.5) ^ ¬既往病史(X, 骨肉瘤)
变量映射: 
  - X: 患者

【规则 3】
规则名: 绝经后妇女特立帕肽绝对禁忌指征
逻辑表达: 用药禁忌(X, 特立帕肽, 绝对) <- 绝经后妇女(X) ^ 患病(X, 骨质疏松) ^ 既往病史(X, 骨肉瘤)
变量映射: 
  - X: 患者

【样例 2：演示多变量 (X, Y) 的图状网络与最高三元限制】
原文："若糖尿病患者的下肢出现溃疡病灶，且该病灶并发深度感染，如果患者对青霉素过敏，则首选克林霉素治疗该溃疡病灶。"
正确输出：
【规则 4】
规则名: 青霉素过敏患者的下肢感染性溃疡首选克林霉素
逻辑表达: 首选治疗(Y, 克林霉素, 针对病灶) <- 糖尿病患者(X) ^ 溃疡病灶(Y) ^ 所属部位(Y, 下肢) ^ 归属患者(Y, X) ^ 并发症状(Y, 深度感染) ^ 过敏史(X, 青霉素)
变量映射: 
  - X: 患者
  - Y: 溃疡病灶

# 任务流程
第一步：在【文本切片】中，寻找【唯一一段】字数超过 100 字的复杂段落。若无满足深度的逻辑（例如全是简单叙述），直接回复“NO_COMPLEX_LOGIC”。
第二步：精确复制这段 100+ 字的原文作为【原始长篇章】。
第三步：对该篇章进行榨取式逻辑建模。每条规则的谓词总数不得少于4个！

# 【终极输出格式约束】
# 1. 绝对禁止“话痨”：不要输出任何形式的思考过程、任务汇报、解释性废话（例如“我已识别出...”、“第一步...”等）。
# 2. 开门见山：你的回复必须、只能以“【原始长篇章】:”开头，随后直接列出规则。
# 3. 严格清洗：除了模板规定的内容，多一个字都会导致系统崩溃！
---
【文本切片】
{text_chunk}
"""

# ==========================================
# 3. 辅助函数
# ==========================================
def get_pdf_text(pdf_path):
    text = ""
    try:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text()
        # 简单清洗多余换行，保持段落连贯性
        text = text.replace('\n', '') 
        return text
    except Exception as e:
        print(f"❌ 无法解析 PDF: {e}")
        return None

def chunk_text(text, chunk_size=1000, overlap_size=150):
    """
    语义切块优化版 (Semantic Chunking)
    按句子边界进行切分，绝对避免把一句话切成两半，并保留完整的上下文重叠区。
    """
    import re
    
    # 1. 消除 PDF 排版导致的强硬回车，保证段落连贯
    text = text.replace('\n', '')
    
    # 2. 按中文/英文的强停顿标点符号分割（保留标点本身）
    # 这里涵盖了句号、问号、叹号、分号
    parts = re.split(r'([。！？；!?;])', text)
    
    # 3. 将文本和标点重新拼合成完整的句子
    sentences = ["".join(i) for i in zip(parts[0::2], parts[1::2])]
    if len(parts) % 2 != 0 and parts[-1].strip():
        sentences.append(parts[-1])
        
    chunks = []
    current_chunk = []
    current_length = 0

    # 4. 贪心算法组装文本块
    for sentence in sentences:
        sentence_len = len(sentence)

        # 发现再装一句就超载了，且当前块不为空，则封口保存当前块
        if current_length + sentence_len > chunk_size and current_length > 0:
            chunks.append("".join(current_chunk))
            
            # 准备下一个块：聪明的 Overlap（重叠区）
            # 从刚才那个块的尾部倒推，挑出几句完整的话带入下一块
            overlap_chunk = []
            overlap_len = 0
            for s in reversed(current_chunk):
                if overlap_len + len(s) <= overlap_size:
                    overlap_chunk.insert(0, s)
                    overlap_len += len(s)
                else:
                    break
                    
            # 兜底：如果连一句话都放不下，就强制带上最后一句
            if not overlap_chunk and current_chunk:
                overlap_chunk = [current_chunk[-1]]
                overlap_len = len(current_chunk[-1])
                
            # 初始化新的块
            current_chunk = overlap_chunk
            current_length = overlap_len

        # 装入当前句子
        current_chunk.append(sentence)
        current_length += sentence_len

    # 把最后剩余的句子保存下来
    if current_chunk:
        chunks.append("".join(current_chunk))
        
    return chunks

def extract_deep_logic(chunk, index, max_retries=1):
    """针对单一文本块进行单点爆破，并带有格式强制校验的重试机制"""
    import re
    
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="deepseek-reasoner",
                messages=[{"role": "user", "content": SNIPER_PROMPT_TEMPLATE.format(text_chunk=chunk)}],
                max_tokens=3000
            )
            result = response.choices[0].message.content.strip()
            
            # 情况 1：确实没有复杂逻辑，直接跳过
            if "NO_COMPLEX_LOGIC" in result:
                print(f"  ⏭️ 文本块 {index} 逻辑密度不足，已跳过。")
                return ""
            
            # 情况 2：格式校验（必须包含原始长篇章和至少一条规则）
            if "【原始长篇章】" not in result or "【规则 1】" not in result:
                print(f"  ⚠️ 文本块 {index} 输出格式不规范（尝试 {attempt+1}/{max_retries}），正在重试...")
                continue # 重新执行循环
                
            # 情况 3：成功捕获
            print(f"  ✅ 文本块 {index} 榨取完毕！成功捕获长段落。")
            # 删除了 "### 来自文本块 ###"，并在结尾加上三个连字符作为每组规则的自然分割
            return f"{result}\n\n---\n\n"
            
        except Exception as e:
            print(f"  ❌ 文本块 {index} 抽取失败（尝试 {attempt+1}/{max_retries}）: {e}")
            time.sleep(2) # 错误后稍微停顿
            
    # 如果重试了 3 次还是失败，只能放弃
    print(f"  🚨 文本块 {index} 连续 {max_retries} 次失败，强制放弃。")
    return ""
# ==========================================
# 4. 主程序 (分块循环 + 并发)
# ==========================================
def main():
    input_dir = "input_pdfs"
    output_dir = "output_rules"
    if not os.path.exists(output_dir): os.makedirs(output_dir)

    for filename in os.listdir(input_dir):
        if filename.lower().endswith(".pdf"):
            print(f"\n🚀 开始处理文档: {filename}")
            raw_text = get_pdf_text(os.path.join(input_dir, filename))
            if not raw_text: continue

            # 1. 物理切片 (每块大概 1000 字)
            chunks = chunk_text(raw_text)
            print(f"✂️ 文档已被切分为 {len(chunks)} 个文本块。")
            
            # 限制最多处理 20个块（响应你的“分8次”需求，避免消耗过大）
            target_chunks = chunks[:12] 
            
            all_rules = []
            print(f"🎯 启动 R1 单点爆破模式，要求 >=100 字，>=4 个谓词...")
            
            # 2. 多线程并发请求 R1
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                future_to_index = {executor.submit(extract_deep_logic, chunk, i+1): i for i, chunk in enumerate(target_chunks)}
                
                for future in concurrent.futures.as_completed(future_to_index):
                    res = future.result()
                    if res:
                        all_rules.append(res)

            # 3. 保存结果
            if all_rules:
                all_rules.sort() # 按块顺序排列
                output_file = os.path.join(output_dir, f"ultimate_rules_{filename.replace('.pdf', '.txt')}")
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write("\n".join(all_rules))
                print(f"🎉 完美收工！深层图式规则已保存至: {output_file}")
            else:
                print("⚠️ 本次未提取到满足硬性条件的复杂规则。")

if __name__ == "__main__":
    main()
