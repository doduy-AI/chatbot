from pathlib import Path

def classify_file(file_path: str) -> str:
    ext = Path(file_path).suffix.lower()
    
    # Doc/Docx
    if ext in [".doc", ".docx"]:
        return "word"
    
    # Ảnh
    elif ext in [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"]:
        return "image"
    
    # PDF → cần detect thêm
    elif ext == ".pdf":
        return detect_pdf_type(file_path)
    
    else:
        return "unsupported"


def detect_pdf_type(file_path: str) -> str:
    import fitz
    doc = fitz.open(file_path)
    total_text = ""
    for page in doc:
        total_text += page.get_text()
    
    return "pdf_word" if len(total_text.strip()) > 100 else "pdf_scan"


if __name__ == "__main__":
    print(classify_file("/home/doduy/Downloads/audio_test/41-2024-qh15.pdf"))