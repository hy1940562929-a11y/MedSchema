import json
import re

def clean_text(text):
    if not isinstance(text, str):
        return text
    
    # 1. 降維打擊：將所有千奇百怪的「陰間空格」強制轉為普通空格
    invisible_spaces = ['\u3000', '\xa0', '\u200b', '\u200c', '\u200d', '\u202c', '\t', '\r', '\n']
    for space in invisible_spaces:
        text = text.replace(space, ' ')
    
    # --- ⚠️ 核彈級數字與單位清洗區 (專治 90 mmHg, 0.1 mU/L, 30 次/分) ⚠️ ---
    
    # 2. 消除 数字 与 英文/中文/希腊字母(如 μ, α, β) 之间的空格
    # \u0370-\u03ff 涵盖了所有希腊字母（完美捕获 μmol）
    text = re.sub(r'([\d.]+)\s+([a-zA-Z\u4e00-\u9fa5\u0370-\u03ff])', r'\1\2', text)
    
    # 3. 消除 英文/中文/希腊字母 与 数字 之间的空格 
    text = re.sub(r'([a-zA-Z\u4e00-\u9fa5\u0370-\u03ff])\s+([\d.]+)', r'\1\2', text)
    
    # 4. 消除 數學符號 與 數字/字母 之間的空格 (全角+半角)
    symbols = r'([<>=≤≥\(\)\[\]\+\-\*／/＜＞（）［］＋－％%])'
    text = re.sub(f'{symbols}\\s+([\\d\\w\u4e00-\u9fa5])', r'\1\2', text)
    text = re.sub(f'([\\d\\w\u4e00-\u9fa5])\\s+{symbols}', r'\1\2', text)
    
    # --- 常規清理區 ---
    
    # 5. 處理底線 "_" 前後的空格 (知識圖譜 URI 專用，如 Concept_ 重症肺炎)
    text = re.sub(r'\s*_\s*', '_', text)
    
    # 6. 消除中文字符與中文字符之間的空格
    text = re.sub(r'([\u4e00-\u9fa5])\s+([\u4e00-\u9fa5])', r'\1\2', text)
    
    # 7. 清除首尾空格，並將殘留的連續空格壓縮為單個
    text = re.sub(r'\s{2,}', ' ', text).strip()
    
    return text

def clean_json_data(data):
    if isinstance(data, dict):
        return {k: clean_json_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_json_data(v) for v in data]
    elif isinstance(data, str):
        return clean_text(data)
    else:
        return data

# 下面的讀寫邏輯保持不變...

if __name__ == "__main__":
    input_file = 'aligned_rules_zh.json'
    output_file = 'aligned_rules_zh_cleaned_v2.json'

    print("正在读取原始文件...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print("正在启动究极正则清洗引擎...")
    cleaned_data = clean_json_data(data)

    print(f"清洗完成，正在保存至 {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
    
    print("大功告成！全角符号和隐藏空格已被彻底剿灭。")