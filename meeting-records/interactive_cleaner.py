#!/usr/bin/env python3

import os
import sys
import subprocess
from pathlib import Path

def get_txt_files():
    """取得 input 目錄中的所有 txt 檔案（排除 archive 目錄）"""
    input_dir = Path("input")
    txt_files = []
    
    for file_path in input_dir.rglob("*.txt"):
        # 排除 archive 目錄中的檔案
        if "archive" not in str(file_path):
            txt_files.append(file_path)
    
    return sorted(txt_files)

def run_cleaner(file_path):
    """執行 cleaner.py 處理指定檔案"""
    try:
        result = subprocess.run(
            ["python3", "cleaner.py", str(file_path)],
            capture_output=True,
            text=True
        )
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), 1

def print_separator():
    """印出分隔線"""
    print("=" * 80)

def print_file_info(file_path, current_index, total_files):
    """印出檔案資訊"""
    progress_percentage = ((current_index + 1) / total_files) * 100
    progress_bar = "█" * int(progress_percentage // 5) + "░" * (20 - int(progress_percentage // 5))
    
    print(f"\n📄 正在處理檔案 {current_index + 1}/{total_files} ({progress_percentage:.1f}%)")
    print(f"📊 進度: [{progress_bar}]")
    print(f"📁 檔案路徑: {file_path.absolute()}")
    print(f"📝 檔案名稱: {file_path.name}")

def show_menu():
    """顯示選項選單"""
    print("\n請選擇下一步動作:")
    print("1. 重新執行此檔案")
    print("2. 執行下一個檔案")
    print("3. 回到上一個檔案")
    print("4. 跳到指定檔案")
    print("5. 列出所有檔案")
    print("6. 退出程式")
    return input("請輸入選項 (1-6): ").strip()

def list_files(files, current_index):
    """列出所有檔案"""
    print("\n所有檔案列表:")
    for i, file_path in enumerate(files):
        marker = " -> " if i == current_index else "    "
        print(f"{marker}{i + 1:2d}. {file_path.name}")

def main():
    # 確認 output 目錄存在
    os.makedirs("output/txt", exist_ok=True)
    os.makedirs("output/csv", exist_ok=True)
    
    # 取得所有要處理的檔案
    txt_files = get_txt_files()
    
    if not txt_files:
        print("在 input 目錄中沒有找到任何 txt 檔案（排除 archive 目錄）")
        return
    
    print(f"找到 {len(txt_files)} 個檔案需要處理")
    
    current_index = 0
    
    while current_index < len(txt_files):
        current_file = txt_files[current_index]
        
        print_separator()
        print_file_info(current_file, current_index, len(txt_files))
        
        # 執行 cleaner.py
        print("\n正在執行 cleaner.py...")
        stdout, stderr, returncode = run_cleaner(current_file)
        
        # 顯示結果
        print("\n執行結果:")
        if returncode == 0:
            print("✅ 執行成功")
            if stdout:
                # 從 stdout 中提取檔案名稱（最後一行通常是 CSV 檔案名）
                lines = stdout.strip().split('\n')
                if lines:
                    # 取最後一行作為檔案名稱
                    csv_filename = lines[-1].strip()
                    if csv_filename.endswith('_output.csv'):
                        # 將 .csv 改為 .txt 來得到 txt 檔案名稱
                        txt_filename = csv_filename.replace('_output.csv', '.txt')
                        txt_path = Path("output/txt/new") / txt_filename
                        
                        print(f"📄 生成的 TXT 檔案: {txt_path.absolute()}")
                        print(f"📊 生成的 CSV 檔案: {Path('output/csv') / csv_filename}")
                        
                        # 檢查檔案是否確實存在
                        if txt_path.exists():
                            print("✅ TXT 檔案已成功生成")
                        else:
                            print("⚠️  TXT 檔案可能未成功生成")
                    else:
                        print("其他輸出:", stdout)
                else:
                    print("無輸出內容")
        else:
            print("❌ 執行失敗")
            if stderr:
                print("錯誤:", stderr)
        
        # 顯示選單並取得使用者選擇
        while True:
            choice = show_menu()
            
            if choice == "1":
                # 重新執行此檔案
                break
            elif choice == "2":
                # 執行下一個檔案
                current_index += 1
                break
            elif choice == "3":
                # 回到上一個檔案
                if current_index > 0:
                    current_index -= 1
                else:
                    print("已經是第一個檔案了")
                    continue
                break
            elif choice == "4":
                # 跳到指定檔案
                list_files(txt_files, current_index)
                try:
                    target = int(input(f"請輸入檔案編號 (1-{len(txt_files)}): ")) - 1
                    if 0 <= target < len(txt_files):
                        current_index = target
                        break
                    else:
                        print("無效的檔案編號")
                except ValueError:
                    print("請輸入有效的數字")
            elif choice == "5":
                # 列出所有檔案
                list_files(txt_files, current_index)
            elif choice == "6":
                # 退出程式
                print("程式結束")
                return
            else:
                print("無效的選項，請重新選擇")
    
    print_separator()
    print("所有檔案處理完成！")

if __name__ == "__main__":
    main()