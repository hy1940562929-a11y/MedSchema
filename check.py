import os
import json
import time
import re
from openai import OpenAI

# ==========================================
# 1. 配置参数
# ==========================================
LOCAL_API_KEY = "not-needed"
LOCAL_BASE_URL = "http://172.18.196.35:1234/v1"
LOCAL_MODEL_NAME = "qwen3.6-35b-a3b" 

DEEPSEEK_API_KEY = "sk-dee462b3e8ed45c4b5df7c6f8905c0d3"
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
TEST_DATA_DIR = "check.jsonl"

local_client = OpenAI(api_key=LOCAL_API_KEY, base_url=LOCAL_BASE_URL)
judge_client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

# ==========================================
# 2. 裁判模型的“思维链”系统提示词 (极大提升准确率)
# ==========================================
JUDGE_SYSTEM_PROMPT = """你是一个专业的“神经符号逻辑裁判”。
你的任务是评估单个【文本段落】下的多条逻辑规则，对比【金标准】和【模型预测】，并统计 TP, FP, FN。

【核心评估尺度：语义等价即为真】：
不要死扣谓词的字眼！只要【模型预测】的规则在“语义”和“因果拓扑关系”上能够覆盖【金标准】的意图，即可判定为匹配成功 (TP)。
1. 谓词同义词宽容：例如金标准为 `HCC患者(X)`，预测为 `患病(X, 肝细胞癌)`，只要指代同一实体，视为等价。
2. 论元精简宽容：例如金标准为 `治疗推荐(X, TACE, 延长总体生存期)`，预测为 `推荐治疗(X, TACE)`，只要核心因果关系成立，可算作匹配。
3. 条件拆分合并：预测规则即使把金标准的一个长条件拆成了两个短条件，只要最终推导逻辑一致，视为 TP。
4. 严格底线 (FP/FN)：如果核心实体搞错、因果关系反转、遗漏了致命的否定算子(¬)，或者预测了原文根本没有的逻辑，才判定为预测无效。

【强制输出格式】：
必须且只能输出合法的 JSON 对象，不要输出任何 Markdown 标记或多余的文字：
{
  "details": [
    {"gold_rule": "金标准规则名", "status": "TP / FN", "reason": "简要判断理由"},
    {"predicted_rule": "预测的多余规则", "status": "FP", "reason": "属于过度提取或幻觉"}
  ],
  "paragraph_TP": 1,
  "paragraph_FP": 0,
  "paragraph_FN": 1
}
"""

# ==========================================
# 3. 核心功能函数
# ==========================================
def extract_rules_from_local_model(system_prompt, user_prompt):
    try:
        response = local_client.chat.completions.create(
            model=LOCAL_MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1, 
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"本地模型调用失败: {e}")
        return ""

def ask_deepseek_judge(gold_standard, predicted_rules):
    judge_prompt = f"""请严格对比以下【同一个文本段落】产生的两组 Datalog 逻辑规则，进行逐条分析并统计得分。

【金标准规则 (Ground Truth)】：
{gold_standard}

【大模型预测的规则 (Predicted)】：
{predicted_rules}
"""
    try:
        response = judge_client.chat.completions.create(
            model="deepseek-chat", 
            messages=[
                {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                {"role": "user", "content": judge_prompt}
            ],
            temperature=0.0, 
            response_format={"type": "json_object"} 
        )
        result_text = response.choices[0].message.content.strip()
        result_text = re.sub(r"```json\n|\n```|```", "", result_text).strip()
        return json.loads(result_text)
    except Exception as e:
        print(f"DeepSeek 裁判打分失败: {e}")
        return {"paragraph_TP": 0, "paragraph_FP": 0, "paragraph_FN": 0}

def load_test_dataset(data_path):
    """智能加载测试数据，支持传入单个 JSONL 文件或包含多个文件的文件夹"""
    dataset = []
    if not os.path.exists(data_path):
        print(f"❌ 找不到路径: {data_path}")
        return dataset
        
    # 收集需要处理的文件列表
    files_to_process = []
    
    # 情况 1：如果你传入的是一个单独的文件 (比如 check.jsonl)
    if os.path.isfile(data_path):
        files_to_process.append(data_path)
    # 情况 2：如果你传入的是一个文件夹
    elif os.path.isdir(data_path):
        for filename in os.listdir(data_path):
            if filename.endswith(".json") or filename.endswith(".jsonl"):
                files_to_process.append(os.path.join(data_path, filename))
                
    # 遍历并解析文件
    for file_path in files_to_process:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line: 
                    continue
                try:
                    data = json.loads(line)
                    if "messages" in data and len(data["messages"]) >= 3:
                        dataset.append(data)
                except json.JSONDecodeError:
                    pass
                    
    return dataset

# ==========================================
# 4. 主执行流：段落级计分与全局 P-R-F1 计算
# ==========================================
if __name__ == "__main__":
    test_dataset = load_test_dataset(TEST_DATA_DIR)
    if not test_dataset:
        print("❌ 测试集为空，请检查路径。")
        exit()

    # 定义全局统计变量
    global_TP = 0
    global_FP = 0
    global_FN = 0

    print(f"🚀 开始评测本地模型，共 {len(test_dataset)} 个文本段落")
    print("-" * 50)

    for i, data in enumerate(test_dataset):
        messages = data["messages"]
        sys_prompt = messages[0]["content"]
        user_prompt = messages[1]["content"] 
        gold_rules = messages[2]["content"]

        print(f"\n▶ 正在处理第 [{i+1}/{len(test_dataset)}] 个文本段落...")
        
        # 1. 本地模型抽取该段落的规则
        predicted_rules = extract_rules_from_local_model(sys_prompt, user_prompt)
        
        # 2. 裁判对该段落进行打分
        scores = ask_deepseek_judge(gold_rules, predicted_rules)
        
        # 3. 将大模型对当前文本段落的打分记在【段落变量】上
        paragraph_TP = scores.get('paragraph_TP', 0)
        paragraph_FP = scores.get('paragraph_FP', 0)
        paragraph_FN = scores.get('paragraph_FN', 0)
        
        print(f"   该段落得分明细: TP={paragraph_TP}, FP={paragraph_FP}, FN={paragraph_FN}")

        # 4. 将该文本段落的变量累加到全局变量中
        global_TP += paragraph_TP
        global_FP += paragraph_FP
        global_FN += paragraph_FN
        
        time.sleep(1.5) 

    # ==========================================
    # 5. 使用全局变量计算最终的 P-R-F1
    # ==========================================
    print("\n" + "=" * 50)
    print("🎉 评测完成！全局统计结果：")
    print(f"最终累计 TP: {global_TP}")
    print(f"最终累计 FP: {global_FP}")
    print(f"最终累计 FN: {global_FN}")
    
    precision = global_TP / (global_TP + global_FP) if (global_TP + global_FP) > 0 else 0
    recall = global_TP / (global_TP + global_FN) if (global_TP + global_FN) > 0 else 0
    f1_score = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    print("-" * 50)
    print(f"🎯 最终 Precision (精确率): {precision * 100:.2f}%")
    print(f"🎯 最终 Recall    (召回率): {recall * 100:.2f}%")
    print(f"🏆 最终 F1-Score  (F1 值) : {f1_score * 100:.2f}%")
    print("=" * 50)