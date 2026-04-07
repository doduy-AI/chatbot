import pymupdf4llm
from pathlib import Path

def pdf_word_to_markdown(filepath: str) -> str:
    try:
        md_conten = pymupdf4llm.to_markdown(filepath)
        return md_conten
    except Exception as e : 
        print("lỗi đọc", filepath)
        return ""
    
def pdf_scan_to_markdown(filepath: str) ->str:
    print("dã cjayujk vào đây")


if __name__ == "__main__":
    file_path = "/home/doduy/Downloads/audio_test/41-2024-qh15.pdf"
    
    md_content = pdf_word_to_markdown(file_path)
    
    output_path = Path(file_path).with_suffix(".md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    
    print(f"Đã lưu: {output_path}")
