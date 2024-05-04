#!/usr/bin/env python3

import re
import os
from pathlib import Path
import sys
import csv

def read_file(file_path):
  if os.path.exists(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    return content
  else:
    return None

def roc_to_western_date(line):
    match = re.match(r'^(.*?)(?:中華民國)?(\d+)年(\d+)月(\d+)日(.*)$', line.replace(' ', ''))
    if match:
        part1 = match.group(1) # 第一段
        year = int(match.group(2))  # 年份 112
        month = match.group(3)  # 月 5
        day = match.group(4)  # 日 24
        part2 = match.group(5)  # 第二段
        if year < 1911:
            year += 1911
        line = f'{part1}{year}年{month}月{day}日{part2}'
    return line

def format_speaker(line):
    patterns = [
        r'^(主席)[:：][\(（](\D+?議員\D+?)[\)）]$',
        r'^(主席)[\(（](\D+?議員\D+?)[\)）][:：]$',
        r'^(\D+?議員\D+?)[:：]$',
        r'^(\D+?市長\D+?)[:：]$',
        r'^(\D+?代理局長\D+?)[:：]$',
        r'^(\D+?副局長\D+?)[:：]$',
        r'^(\D+?分局長\D+?)[:：]$',
        r'^(\D+?局長\D+?)[:：]$',
        r'^(\D+?處長\D+?)[:：]$',
        r'^(\D+?代理科長\D+?)[:：]$',
        r'^(\D+?科長\D+?)[:：]$',
        r'^(\D+?代理區長\D+?)[:：]$',
        r'^(\D+?區長\D+?)[:：]$',
        r'^(\D+?主任委員\D+?)[:：]$',
        r'^(\D+?主任秘書\D+?)[:：]$',
        r'^(\D+?主任\D+?)[:：]$',
        r'^(\D+?所長\D+?)[:：]$'
    ]

    for pattern in patterns:
        match = re.match(pattern, line)
        if match:
            groups = match.groups()
            if len(groups) == 2:
                chairman, name = groups
                formatted_name = re.sub(r'(.+)議員(.+)', r'\1\2議員', name)
                return f"{chairman}{formatted_name}："
            else:
                name = groups[0]
                parts = re.split(r'(議員|市長|代理局長|副局長|分局長|局長|代理科長|科長|代理區長|區長|主任委員|主任秘書|主任|所長|處長)', name)
                formatted_name = ''.join([parts[0], parts[2], parts[1]]) + '：'
                return formatted_name
    return line

def split_speaker_line(line):
    patterns = [
        r'^(主席[:：][\(（]\D+?議員\D+?[\)）])(.*)$',
        r'^(\D+?議員\D{1,3}?[:：])(.*)$',
        r'^(\D+?市長\D{1,3}[:：])(.*)$',
        r'^(\D+?代理局長\D{1,3}[:：])(.*)$',
        r'^(\D+?副局長\D{1,3}[:：])(.*)$',
        r'^(\D+?分局長\D{1,3}[:：])(.*)$',
        r'^(\D+?局長\D{1,3}[:：])(.*)$',
        r'^(\D+?處長\D{1,3}[:：])(.*)$',
        r'^(\D+?代理科長\D{1,3}[:：])(.*)$',
        r'^(\D+?科長\D{1,3}[:：])(.*)$',
        r'^(\D+?區長\D{1,3}[:：])(.*)$',
        r'^(\D+?代理區長\D{1,3}[:：])(.*)$',
        r'^(\D+?所長\D{1,3}[:：])(.*)$',
        r'^(\D+?主任委員\D{1,3}[:：])(.*)$',
        r'^(\D+?主任秘書\D{1,3}[:：])(.*)$',
        r'^(\D+?主任\D{1,3}[:：])(.*)$'
    ]

    for pattern in patterns:
        match = re.match(pattern, line)
        if match:
            speaker, content = match.groups()
            if len(speaker) > 12:
                print(match.groups())
            speaker = format_speaker(speaker)
            content = content.strip()
            if content:
                return [speaker, content]
            else:
                return [speaker]
    return [line.strip()]

def process_record_list(record_list):
    processed_list = []
    current_line = ''
    end_chars = ('？', '?', '!', '！', '：', '。', '）', ')', '…', '】')
    for line in record_list:
        if any(line.endswith(char) for char in end_chars):
            current_line += line
            processed_list.extend(split_speaker_line(current_line))
            current_line = ''
        else:
            current_line += line
    if current_line:
        processed_list.extend(split_speaker_line(current_line))
    # print(processed_list)
    return processed_list



def process_text(text):
    # 1. 用\n切開文字,每行先用strip處理,並移除空白的行
    lines = [line.strip() for line in text.split('\n') if line.strip()]

    # 3. 如果有哪一行只有數字,表示是頁碼,請移除
    lines = [line for line in lines if not line.isdigit()]
    lines = [line for line in lines if not re.match(r'^第.*　\d+$', line)]
    meeting_title_prefix = ''
    if re.match(r'^臺南市議會第\d+屆第\d+次(定期會|臨時會)會議紀錄$', lines[0].strip().replace(' ', '')):
        meeting_title_prefix = lines[0].strip().replace(' ', '').replace('會議紀錄', '').replace('臺南市議會', '')
        del lines[0:1]
    # print(lines[0])
    # 2. 第一行有東西的是page_title,之後如果遇到有哪一行內容跟page_title相同,就移除
    if '部門業務報告及質詢' in lines[0]:
        meeting_title = lines[0].replace(' ', '').replace('」', '').replace('「', '')
        match = re.search(r'(\d{1,4}年\d{1,2}月\d{1,2}日)', meeting_title)
        if match:
            meeting_date = match.group(1)
            new_meeting_date = roc_to_western_date(meeting_date)
            lines.insert(1, new_meeting_date)
            meeting_title = meeting_title.replace(meeting_date, new_meeting_date)
        meeting_title = meeting_title_prefix + meeting_title
        lines[0] = meeting_title
        # print(meeting_title)
    elif '會議紀錄' in lines[0]:
        meeting_title = lines[0].split('會議紀錄')[0].strip() + '會議紀錄'
        meeting_date = lines[0].split('會議紀錄')[1].strip()
        lines.insert(1, meeting_date)
    elif '專案報告' in lines[0]:
        first_line = lines[0]
        meeting_title = first_line.split('專案報告')[0].strip() + '專案報告'
        meeting_date = first_line.split('專案報告')[1].strip().replace('(', '').replace(')', '')
        lines[0] = meeting_title
        lines.insert(1, meeting_date)
        print(meeting_title)
    elif '會議紀錄' not in lines[0] and len(lines[0]) < 40:
        page_title = lines[0]
        lines = [line for line in lines[1:] if line != page_title]

        # 4. 第二行是會議標題meeting_title,請保存下來
        meeting_title = lines[0]
    elif re.match(r'^(第\d+屆第\d+次\D*?)(\d+)年(\d+)月(\d+)日(\(第?\d+次會議\))$', lines[0].replace(' ', '')):
        # 第4屆第1次定期會市政總質詢112年5月24日(第2次會議)
        match = re.match(r'^(第\d+屆第\d+次\D*?)(\d+)年(\d+)月(\d+)日(\(第?\d+次會議\))$', lines[0].replace(' ', ''))
        part1 = match.group(1)  # 第4屆第1次定期會市政總質詢
        year = match.group(2)  # 年份 112
        month = match.group(3)  # 月 5
        day = match.group(4)  # 日 24
        meeting = match.group(5)  # (第2次會議)
        meeting_title = f'{part1}{meeting}'
        meeting_date = f'{year}年{month}月{day}日'
        del lines[0:1]
        lines.insert(0, meeting_title)
        lines.insert(1, meeting_date)
    elif len(lines[0]) >= 40 and (lines[1].strip().endswith('日') or lines[1].strip().endswith('日)')):
        first_line = ''.join(lines[0:2])
        del lines[0:2]
        if '會議紀錄' in first_line:
            meeting_title = first_line.split('會議紀錄')[0].strip() + '會議紀錄'
            meeting_date = first_line.split('會議紀錄')[1].strip().replace('(', '').replace(')', '')
        # elif '專案報告' in first_line:
        else:
            meeting_title = first_line.split('專案報告')[0].strip() + '專案報告'
            meeting_date = first_line.split('專案報告')[1].strip().replace('(', '').replace(')', '')
        lines.insert(0, meeting_title)
        lines.insert(1, meeting_date)
    else:
        # print(lines[0])
        if '會議紀錄' in lines[0]:
            meeting_title = lines[0].split('會議紀錄')[0].strip() + '會議紀錄'
            meeting_date = lines[0].split('會議紀錄')[1].strip()
        else:
            meeting_title = lines[0].split('專案報告')[0].strip() + '專案報告'
            meeting_date = lines[0].split('專案報告')[1].strip()
        lines.insert(1, meeting_date)

    # 5. 接下來會有好幾行,只要沒有看到「主席」開頭,就先存在另外一個info_list裡面
    info_list = []
    i = 1
    # print(lines[:3])
    while i < len(lines) and not lines[i].startswith('主席'):
        if re.search(r'(\d+)年(\d+)月(\d+)日', lines[i].replace(' ', '')):
            info_list.append(roc_to_western_date(lines[i].replace(' ', '')))
        else:
            info_list.append(lines[i])
        i += 1

    # 6. 一旦看到「主席」開頭,就表示會議開始,請存在record_list裡面
    record_list = []
    while i < len(lines) and not lines[i] == '(附件)':
        record_list.append(lines[i])
        if lines[i].endswith('散會。') or lines[i].endswith('散會！'):
            break
        i += 1
    # print(record_list[:3])
    # 7. 一旦看到「(附件)」,代表會議結束,後續可以不要處理
    meeting_title = meeting_title.replace(' ', '')
    # 8. 回傳meeting_title、info_list、record_list
    return meeting_title, info_list, record_list

def record_list_to_output(processed_list):
    speaker_pattern = r'^(主席|\D+?議員|\D+?市長|\D+?代理局長|\D+?副局長|\D+?局長|\D+?處長|\D+?代理科長|\D+?科長|\D+?代理區長|\D+?區長|\D+?主任委員|\D+?主任秘書|\D+?主任|\D+?所長)[:：]$'
    speaker = None
    result_txt = []
    result_csv = []
    for line in processed_list:
        match = re.match(speaker_pattern, line)
        if match:
            speaker = line.replace('：', '')
        else:
            result_txt.append("%s：%s" % (speaker, line))
            result_csv.append({
                'speaker': speaker,
                'content': line
            })
    return result_txt, result_csv

def save_file(content, file_path):
    if isinstance(content, list):
        content = "\n\n".join(str(item) for item in content)
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)

def save_csv_file(csv_data, file_path):
    fieldnames = csv_data[0].keys()
    with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()

        for row in csv_data:
            writer.writerow(row)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py filename")
    else:
        input_filename = sys.argv[1]
        if not os.path.exists(input_filename):
            print('請確認檔案位址。')
            sys.exit(1)
        text = read_file(input_filename)
        base_name = Path(input_filename).stem
        meeting_title, info_list, record_list = process_text(text)
        record_list = process_record_list(record_list)
        record_list, result_csv = record_list_to_output(record_list)
        result_list = [meeting_title] + info_list + record_list
        save_file(result_list, 'output/txt/' + meeting_title + '_output.txt')
        save_csv_file(result_csv, 'output/csv/' + meeting_title + '_output.csv')

