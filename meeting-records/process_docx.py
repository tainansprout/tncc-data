#!/usr/bin/env python3


import os
import re
from pathlib import Path
from docx import Document
import sys

def is_meeting_record_file(filename):
    """判斷檔名是否可能為會議記錄檔案（寬鬆篩選）"""
    # 明確排除不需要的檔案類型
    exclude_keywords = [
        '提案單', '程序委員會', '決議案', '每日刪減表',
        '大會第', '墊付款案', '聯席審查', '委員會議案審查'
    ]
    for keyword in exclude_keywords:
        if keyword in filename:
            return False
    
    # 檔名檢查改為寬鬆模式，主要靠內容檢測
    # 只要不是明確排除的檔案，都允許進入內容檢測
    return True

def extract_text_from_docx(docx_path):
    """從docx檔案提取純文字內容"""
    try:
        doc = Document(docx_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        print(f"讀取 {docx_path} 時發生錯誤: {e}")
        return None

def has_speech_content(text):
    """檢測文字是否包含發言記錄內容"""
    if not text:
        return False
    
    # 根據archive檔案分析，真正的發言記錄應該有以下特徵：
    
    # 1. 檢查主席發言格式
    chairman_patterns = [
        r'^主席[:：]',                    # 主席：
        r'^主席[\(（][^)）]*[\)）][:：]',   # 主席（某某議員）：
        r'主席[\(（][^)）]*[\)）][:：]',    # 其他位置的主席（某某議員）：
    ]
    chairman_matches = 0
    for pattern in chairman_patterns:
        matches = re.findall(pattern, text, re.MULTILINE)
        chairman_matches += len(matches)
    
    # 2. 檢查議員發言格式 (基於archive的真實pattern)
    speaker_patterns = [
        r'^[\w\s]+議員[\w\s]*[:：]',     # 某某議員：
        r'^[\w\s]+市長[\w\s]*[:：]',     # 某某市長：
        r'^[\w\s]+局長[\w\s]*[:：]',     # 某某局長：
        r'^[\w\s]+處長[\w\s]*[:：]',     # 某某處長：
        r'^[\w\s]+科長[\w\s]*[:：]',     # 某某科長：
        r'^[\w\s]+主任[\w\s]*[:：]',     # 某某主任：
        r'^[\w\s]+副局長[\w\s]*[:：]',   # 某某副局長：
        r'^[\w\s]+代理局長[\w\s]*[:：]', # 某某代理局長：
    ]
    
    speaker_matches = 0
    for pattern in speaker_patterns:
        matches = re.findall(pattern, text, re.MULTILINE)
        speaker_matches += len(matches)
    
    # 3. 檢查是否有質詢內容的特徵詞
    content_indicators = [
        '質詢', '報告', '請教', '請問', '謝謝', '議員', '市長', '局長',
        '主席', '會議', '發言', '問題', '回答', '說明'
    ]
    
    content_score = 0
    for indicator in content_indicators:
        if indicator in text:
            content_score += 1
    
    # 4. 檢查文件長度（真正的會議記錄通常較長）
    content_length = len(text.strip())
    has_substantial_content = content_length > 2000  # 至少2000字符
    
    # 5. 檢查是否有議員質詢順序（常見於會議記錄開頭）
    has_agenda_info = bool(re.search(r'議員質詢順序|記錄[:：]|會議.*日', text))
    
    # 判斷條件（降低門檻以包含更多有效檔案）：
    # - 有主席發言 OR 有大量發言人記錄
    # - 必須有至少10個發言人記錄
    # - 必須有足夠的內容指標
    # - 必須有實質內容長度
    has_sufficient_speech = ((chairman_matches >= 1 or speaker_matches >= 50) and 
                           speaker_matches >= 10 and 
                           content_score >= 3 and
                           has_substantial_content)
    
    print(f"    檢測結果: 主席發言({chairman_matches}) 發言人({speaker_matches}) 內容指標({content_score}) 長度({content_length}) 議程({has_agenda_info})")
    
    return has_sufficient_speech

def extract_meeting_info(text, filename):
    """從內容和檔名提取會議資訊"""
    # 先從檔名嘗試提取會議資訊
    meeting_info = extract_info_from_filename(filename)
    
    # 從內容中尋找會議標題和日期
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    if not lines:
        return meeting_info
    
    # 尋找會議標題
    for i, line in enumerate(lines[:10]):  # 檢查前10行
        # 檢查是否為會議標題格式
        if ('第' in line and '屆' in line and ('次' in line or '會' in line)) or \
           ('市政總質詢' in line) or ('業務報告及質詢' in line) or ('專案報告' in line):
            meeting_info['title'] = line
            break
    
    # 尋找日期
    date_pattern = r'(\d{4}年\d{1,2}月\d{1,2}日|\d{1,3}年\d{1,2}月\d{1,2}日)'
    for line in lines[:15]:  # 檢查前15行
        date_match = re.search(date_pattern, line)
        if date_match:
            date_str = date_match.group(1)
            # 轉換民國年為西元年
            if len(date_str.split('年')[0]) <= 3:
                year_part = int(date_str.split('年')[0])
                if year_part < 1911:
                    year_part += 1911
                    date_str = date_str.replace(date_match.group(1).split('年')[0], str(year_part))
            meeting_info['date'] = date_str
            break
    
    return meeting_info

def extract_info_from_filename(filename):
    """從檔名提取基本資訊"""
    info = {'title': '', 'date': '', 'session': '', 'meeting_type': ''}
    
    # 提取日期 (YYYYMMDD 格式)
    date_match = re.search(r'(\d{8})', filename)
    if date_match:
        date_str = date_match.group(1)
        year = date_str[:4]
        month = date_str[4:6]
        day = date_str[6:8]
        info['date'] = f"{year}年{month}月{day}日"
    
    # 提取會議類型
    if '市政總質詢' in filename:
        info['meeting_type'] = '市政總質詢'
    elif '業務報告及質詢' in filename:
        info['meeting_type'] = '業務報告及質詢'
    elif '專案報告' in filename:
        info['meeting_type'] = '專案報告'
    elif '會議紀錄' in filename:
        info['meeting_type'] = '會議紀錄'
    
    return info

def generate_output_filename(meeting_info, original_filename):
    """生成輸出檔名，符合既有命名規則"""
    # 建立基礎檔名
    if meeting_info.get('title'):
        base_name = meeting_info['title']
    else:
        # 根據檔名資訊建構標題
        if meeting_info.get('meeting_type'):
            base_name = f"第4屆第4次定期會{meeting_info['meeting_type']}"
            if meeting_info.get('date'):
                base_name += meeting_info['date']
        else:
            # 使用原檔名去除副檔名
            base_name = Path(original_filename).stem
    
    # 清理檔名中的特殊字符
    base_name = re.sub(r'[^\w\u4e00-\u9fff\-\(\)（）]', '', base_name)
    
    return base_name + '.txt'

def scan_docx_files(raw_directory):
    """掃描raw目錄中的所有docx檔案"""
    docx_files = []
    
    for root, dirs, files in os.walk(raw_directory):
        for file in files:
            if file.endswith('.docx') and not file.startswith('~$'):  # 排除臨時檔案
                file_path = os.path.join(root, file)
                docx_files.append(file_path)
    
    return docx_files

def process_docx_files(raw_directory, output_directory):
    """處理docx檔案並轉換為txt"""
    # 確保輸出目錄存在
    os.makedirs(output_directory, exist_ok=True)
    
    # 掃描所有docx檔案
    docx_files = scan_docx_files(raw_directory)
    print(f"找到 {len(docx_files)} 個 docx 檔案")
    
    processed_count = 0
    filtered_count = 0
    
    for docx_path in docx_files:
        filename = os.path.basename(docx_path)
        print(f"\n檢查檔案: {filename}")
        
        # 1. 檢查檔名是否為會議記錄
        if not is_meeting_record_file(filename):
            print(f"  ❌ 檔名不符合會議記錄格式，跳過")
            continue
        
        # 2. 提取內容
        text_content = extract_text_from_docx(docx_path)
        if not text_content:
            print(f"  ❌ 無法讀取檔案內容，跳過")
            continue
        
        # 3. 檢查是否包含發言記錄
        if not has_speech_content(text_content):
            print(f"  ❌ 不含發言記錄內容，跳過")
            filtered_count += 1
            continue
        
        # 4. 提取會議資訊
        meeting_info = extract_meeting_info(text_content, filename)
        
        # 5. 生成輸出檔名
        output_filename = generate_output_filename(meeting_info, filename)
        output_path = os.path.join(output_directory, output_filename)
        
        # 6. 檢查檔案是否已存在
        if os.path.exists(output_path):
            print(f"  ⚠️  檔案已存在: {output_filename}，跳過")
            continue
        
        # 7. 寫入txt檔案
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text_content)
            print(f"  ✅ 成功轉換: {output_filename}")
            processed_count += 1
        except Exception as e:
            print(f"  ❌ 寫入檔案失敗: {e}")
    
    print(f"\n處理完成:")
    print(f"  成功轉換: {processed_count} 個檔案")
    print(f"  過濾掉: {filtered_count} 個檔案")
    print(f"  總檢查: {len(docx_files)} 個檔案")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方式: python process_docx.py [raw目錄路徑] [輸出目錄路徑]")
        print("範例: python process_docx.py raw input")
        sys.exit(1)
    
    raw_dir = sys.argv[1] if len(sys.argv) > 1 else "raw"
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "input"
    
    if not os.path.exists(raw_dir):
        print(f"錯誤: 找不到目錄 {raw_dir}")
        sys.exit(1)
    
    print(f"開始處理 {raw_dir} 目錄中的 docx 檔案...")
    print(f"輸出目錄: {output_dir}")
    
    process_docx_files(raw_dir, output_dir)