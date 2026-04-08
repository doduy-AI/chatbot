from pathlib import Path
import os
import shutil
from .classifier import classify_file
from .extract_word import word_to_markdown
from .extract_pdf import pdf_word_to_markdown ,pdf_scan_to_markdown

def extract_text(file_path: str) -> str:
    file_type = classify_file(file_path)
    print(f"[{file_type}]{Path(file_path).name}")

    extractor = {
        "word": lambda: word_to_markdown(file_path),
        "pdf_word": lambda: pdf_word_to_markdown(file_path),
        "pdf_scan": lambda: pdf_scan_to_markdown(file_path),
        "text_ready": lambda: "CLEAR"
    }

    if file_type == "unsupported":
        print(f"[Service] file không được hỗ trợ {file_path}")
        return ""
    
    return extractor[file_type]()

def process_folder_to_markdown(folder_path: str,folder_path_clean:str):
    print(f"[OCR] Đang bắt đầu quyét thư mục {folder_path}")
    print("[ABC]{folder_path_clean}")
    if not os.path.isdir(folder_path):
        print(f"[ROUTER_CLEAR_DATA] : Không tìm thấy thư mục {folder_path}")
        return 
    for file_name in os.listdir(folder_path):
        full_path = os.path.join(folder_path, file_name)
        
        # Chỉ xử lý nếu là file (không phải thư mục con)
        if os.path.isfile(full_path):
            markdown_content = extract_text(full_path)
            
            
            if markdown_content:
                if markdown_content == "CLEAR":
                    shutil.copy2(os.path.join(folder_path,file_name),folder_path_clean)
                    continue
                else:
                    file_stem = Path(file_name).stem 
                    output_file_name = f"{file_stem}.md"
                    output_path = os.path.join(folder_path_clean, output_file_name)
                    with open(output_path, "w", encoding="utf-8") as f:
                        f.write(markdown_content)
                    
                    print(f"    ✓ Đã lưu: {output_path}")
                    print(f"Đã trích xuất xong: {file_name}")