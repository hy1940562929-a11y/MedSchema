import json
import os

# 1. 定义极其严密的系统提示词（包含 Few-shot 示例）
SYSTEM_PROMPT = """你是一位严谨的符号逻辑专家。你的任务是根据给定的【文本切片】，严格按照特定的“图式规则（Schema Rules）”范式，进行文档级一阶逻辑规则（Datalog 风格）提取。

【理论基础与语法约束】
1. 元数绝对限制：谓词最高只能是三元！
   - 一元谓词：用于表示实体类型或状态属性（如 `糖尿病患者(X)`）。规则体中的实体变量必须先用一阶谓词声明。
   - 二元谓词：用于表示实体间的核心图状关系（如 `并发疾病(X, 脓毒症)`、`归属(Y, X)`）。
   - 三元谓词：仅限于用第三个参数（常量）修饰二元关系（如 `用药推荐(X, 胺碘酮, 强烈首选)`）。
2. 禁止嵌套与集合：论元只能是变量（X, Y, Z）或单一常量。绝对禁止谓词嵌套或使用集合。
3. 绝对封杀“或者(OR)”：逻辑表达中绝对不允许出现 `V`、`OR`。遇到原文中的并列/或者条件，必须将其拆分为多条独立、平行的规则！
4. 精准否定：排他性或未发生的前提，必须使用否定符号 `¬`（如 `¬过敏史(X, 青霉素)`）。
5. 结构规范：采用 `[结论/规则头] <- [条件1/规则体] ^ [条件2/规则体] ...` 形式，禁止使用圆括号 `()` 进行逻辑分块。

【终极输出格式约束】
绝对禁止“话痨”，不要输出任何解释性废话或原文复述。必须直接输出规则，每条规则严格包含“规则名”、“逻辑表达”和“变量映射”。

=== 样例 1：演示彻底拆分“OR”与精准否定 ===
【输入文本】：
"对于骨质疏松的绝经后妇女，如果之前发生过脆性骨折或T值低于-2.5，强烈建议使用特立帕肽，但若有骨肉瘤病史则绝对禁用。"
【输出规则】：
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

=== 样例 2：演示多变量 (X, Y) 的图状网络 ===
【输入文本】：
"若糖尿病患者的下肢出现溃疡病灶，且该病灶并发深度感染，如果患者对青霉素过敏，则首选克林霉素治疗该溃疡病灶。"
【输出规则】：
【规则 4】
规则名: 青霉素过敏患者的下肢感染性溃疡首选克林霉素
逻辑表达: 首选治疗(Y, 克林霉素, 针对病灶) <- 糖尿病患者(X) ^ 溃疡病灶(Y) ^ 所属部位(Y, 下肢) ^ 归属患者(Y, X) ^ 并发症状(Y, 深度感染) ^ 过敏史(X, 青霉素)
变量映射: 
  - X: 患者
  - Y: 溃疡病灶
"""

def convert_txt_to_jsonl(input_file, output_file):
    dataset = []
    
    # 读取原始 TXT 文件
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # 按照 '---' 切分每个样本块
    blocks = content.strip().split('---')
    
    for block in blocks:
        block = block.strip()
        if not block:
            continue
            
        # 寻找输入文本（原始长篇章）和输出规则（规则列表）
        if "【原始长篇章】:" in block:
            parts = block.split("【规则 1】", 1)
            
            if len(parts) == 2:
                # 提取并清理输入文本，去掉那些 的标签干扰
                raw_input_text = parts[0].replace("【原始长篇章】:", "").strip()
                import re
                input_text = re.sub(r'\\s*', '', raw_input_text)
                
                # 提取并清理输出规则，同样去掉 source 标签
                raw_output_rule = "【规则 1】\n" + parts[1].strip()
                output_rule = re.sub(r'\\s*', '', raw_output_rule)
                
                # 只要成功提取到了输入和输出，就组装成 ChatML 格式
                if input_text and output_rule:
                    chat_message = {
                        "messages": [
                            {
                                "role": "system",
                                "content": SYSTEM_PROMPT
                            },
                            {
                                "role": "user",
                                "content": f"请仔细解析以下输入文本，提取其中蕴含的因果关系与约束条件，并仅输出合法的逻辑规则表达式，不要包含任何额外的解释性文字：\n【输入文本】：\n{input_text}"
                            },
                            {
                                "role": "assistant",
                                "content": output_rule
                            }
                        ]
                    }
                    dataset.append(chat_message)
            
    # 改为 'a' (追加模式)，确保循环时文件不被覆盖
    with open(output_file, 'a', encoding='utf-8') as f:
        for item in dataset:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
            
    return len(dataset)


if __name__ == "__main__":
    input_dir = "/Users/jakky/Desktop/database/output_rules"
    output_jsonl_path = "/Users/jakky/Desktop/database/finetune_dataset.jsonl"
    
    # 如果输出文件已经存在，先清空它，为后续的追加写入提供干净的环境
    if os.path.exists(output_jsonl_path):
        os.remove(output_jsonl_path)
    
    total_extracted = 0
    
    print("🚀 开始批量转换数据...")
    for filename in os.listdir(input_dir):
        if filename.endswith(".txt"):
            file_path = os.path.join(input_dir, filename)
            try:
                # 调用上面的函数
                count = convert_txt_to_jsonl(file_path, output_jsonl_path)
                total_extracted += count
                print(f"✅ 成功处理: {filename}，提取了 {count} 个篇章的规则组合。")
            except Exception as e:
                print(f"❌ 处理 {filename} 时出错: {e}")
                
    print("-" * 40)
    print(f"🎉 所有文件转换完成！")
    print(f"📊 总计提取了 {total_extracted} 条高质量微调数据（每条包含篇章与多条规则）。")
    print(f"📁 数据已安全保存至: {output_jsonl_path}")