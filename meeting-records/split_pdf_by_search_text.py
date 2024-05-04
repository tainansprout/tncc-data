import fitz  # PyMuPDF
import sys
import os

#  python split_pdf_by_search_text.py 臺南市議會第4屆第1次定期會議事錄.pdf "次會會議紀錄" "」會議紀錄" "次會議)" "部門業務報告及質詢" "會市政總質詢" "」專案報告"

def save_pdf_to_txt(document, output_filename):
    text = ''
    for page in document:
        text += page.get_text() + '\n'
    with open(output_filename, 'w', encoding='utf-8') as out_file:
        out_file.write(text)

def split_pdf_by_text(pdf_path, search_texts, max_pages=100):
    pdf = fitz.open(pdf_path)
    pages_with_text = []

    # 確保 output 目錄存在
    output_dir = os.path.join(os.getcwd(), "output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 遍歷每一頁尋找多個搜尋文字
    for page_num in range(len(pdf)):
        page = pdf.load_page(page_num)
        # 檢查此頁是否包含任何一個搜尋文字
        for search_text in search_texts:
            if page.search_for(search_text):
                print(f"在第 {page_num + 1} 頁找到 '{search_text}'")
                pages_with_text.append(page_num)
                break  # 找到一個就足夠，無需檢查其他搜尋文字

    if pages_with_text:
        pages_with_text.append(len(pdf) - 1)  # 添加最後一頁作為結束點

    # 根據找到的頁面分割PDF
    for i in range(len(pages_with_text) - 1):
        start_page = pages_with_text[i]
        # end_page = min(start_page + max_pages, pages_with_text[i + 1] - 1, len(pdf) - 1)
        end_page = min(pages_with_text[i + 1] - 1, len(pdf) - 1)

        if start_page < end_page:
            print(f"正在儲存從第 {start_page + 1} 頁到第 {end_page + 1} 頁的分割檔案")
            new_doc = fitz.open()
            new_doc.insert_pdf(pdf, from_page=start_page, to_page=end_page)

            file_suffix = "-需要人工檢查" if end_page - start_page + 1 >= max_pages else ""
            new_filename = f"{os.path.splitext(os.path.basename(pdf_path))[0]}-p{start_page+1}-{end_page+1}{file_suffix}"
            new_pdf_filename = new_filename + '.pdf'
            new_txt_filename = new_filename + '.txt'
            full_pdf_path = os.path.join(output_dir, new_pdf_filename)
            full_txt_path = os.path.join(output_dir, new_txt_filename)
            save_pdf_to_txt(new_doc, full_txt_path)
            new_doc.save(full_pdf_path)
            print(f"已儲存: {full_pdf_path}")
            new_doc.close()

    pdf.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("使用方式: python split_pdf_by_search_text.py <PDF路徑> '<搜尋文字1>' '<搜尋文字2>' ...")
        # "次會會議紀錄" "」會議紀錄" "次會議)" "部門業務報告及質詢" "會市政總質詢" "」專案報告"
        sys.exit(1)

    pdf_path = sys.argv[1]
    search_texts = sys.argv[2:]
    split_pdf_by_text(pdf_path, search_texts)
