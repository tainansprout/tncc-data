import pandas as pd

def correct_name_case(name):
    # 分割名字並轉換大小寫
    parts = name.lower().split(", ")
    # 首字母大寫處理，適用於姓和名
    corrected_parts = [part.title() for part in parts]
    # 重新組合成完整名字
    return ", ".join(corrected_parts)

def format_districts(districts):
    # 分割地名
    names = districts.split('.')
    # 添加「區」後綴（如果尚未有）
    formatted_names = [name if name.endswith('區') else name + '區' for name in names]
    # 使用中文頓號連接地名
    return '、'.join(formatted_names)

party_dict = {
    '基進': '基進黨',
    '無盟': '無黨團結聯盟',
    '無': '無黨籍',
    '民': '民主進步黨',
    '國': '中國國民黨',
    '台聯': '台灣團結聯盟'
}

# 讀取第一個CSV
address_book_df = pd.read_csv('input/address_book.csv')

address_book_df['黨籍'] = address_book_df ['黨籍'].replace(party_dict)

address_book_df['區別'] = address_book_df['區別'].apply(format_districts)

# 在電話號碼前添加 '06-'
address_book_df['服務處電話'] = '06-' + address_book_df['服務處電話'].astype(str)
address_book_df['傳真電話'] = '06-' + address_book_df['傳真電話'].astype(str)

# 使姓名能夠一致化
address_book_df['姓名'] = address_book_df['姓名'].str.strip().str.replace(r'\s+', ' ', regex=True)

# 檢查修改後的數據
print(address_book_df.head())

# 讀取第二個CSV
english_name_df = pd.read_csv('input/english_name.csv')

# 使英文名可以有正確的大小寫
english_name_df['英文名'] = english_name_df['英文名'].apply(correct_name_case)

# 使姓名能夠一致化
english_name_df['姓名'] = english_name_df['姓名'].str.strip().str.replace(r'\s+', ' ', regex=True)

# 檢查數據
print(english_name_df.head())

# 合併兩個DataFrame
address_book_df = pd.merge(address_book_df, english_name_df, on='姓名')

address_book_df = address_book_df[['職稱','黨籍','姓名','英文名','區別','郵遞區號','服務處地址','服務處電話','傳真電話']]

# 檢查合併後的數據
print(address_book_df.head())

# 輸出到新的檔案
address_book_df.to_csv('output/csv/address_book.csv', index=False)
address_book_df.to_json('output/json/address_book.json', orient='records', indent=2, force_ascii=False)
