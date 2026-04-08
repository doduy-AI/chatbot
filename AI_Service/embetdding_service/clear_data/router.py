from pathlib import Path
from .classifier import classify_file
from .extract_word import word_to_markdown
from .extract_pdf import pdf_word_to_markdown ,pdf_scan_to_markdown

def extract_text(file_path: str) -> str:
    file_type = classify_file(file_path)
    print(f"[{file_type}]{Path(file_path).name}")

    extractor = {
        "word": lambda: word_to_markdown(file_path),
        "pdf_word": lambda: pdf_word_to_markdown(file_path),
        "pdf_scan": lambda: pdf_word_to_markdown(file_path)
    }

    if file_type == "unsupported":
        print(f"[Service] file không được hỗ trợ {file_path}")
        return ""
    
    return extractor[file_type]()