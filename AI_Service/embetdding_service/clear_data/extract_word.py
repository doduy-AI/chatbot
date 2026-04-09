import subprocess
import tempfile
import shutil
from pathlib import Path
import re


def convert_doc_to_docx(file_path: str) -> tuple[str, str | None]:
    file_path = Path(file_path)
    
    if file_path.suffix.lower() == ".docx":
        return str(file_path), None
    
    tmp_dir = tempfile.mkdtemp()
    
    # Copy sang tên không có dấu cách để LibreOffice không bị lỗi
    safe_name = "input.doc"
    safe_input = Path(tmp_dir) / safe_name
    shutil.copy2(str(file_path), str(safe_input))
    
    result = subprocess.run(
        [
            "libreoffice", "--headless",
            "--convert-to", "docx",
            "--outdir", tmp_dir,
            str(safe_input)
        ],
        capture_output=True, text=True, timeout=60
    )
    
    if result.returncode != 0:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise RuntimeError(f"LibreOffice lỗi: {result.stderr}")
    
    output_file = Path(tmp_dir) / "input.docx"
    if not output_file.exists():
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise FileNotFoundError(f"Không tìm thấy output: {output_file}")
    
    return str(output_file), tmp_dir


def word_to_markdown(file_path: str) -> str:
    tmp_dir = None
    
    try:
        file_path_obj = Path(file_path)
        
        if file_path_obj.suffix.lower() == ".doc":
            docx_path, tmp_dir = convert_doc_to_docx(file_path)
        else:
            docx_path = file_path
        
        # Dùng -t plain để pandoc tự bỏ hết table markup
        result = subprocess.run(
            ["pandoc", docx_path, "-t", "plain", "--wrap=none"],
            capture_output=True, text=True, timeout=120
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Pandoc lỗi: {result.stderr}")
        
        return clean_text(result.stdout)
    
    except Exception as e:
        print(f"  Lỗi đọc file word {file_path}: {e}")
        return ""
    
    finally:
        if tmp_dir:
            shutil.rmtree(tmp_dir, ignore_errors=True)


def clean_text(text: str) -> str:
    lines = text.splitlines()
    cleaned = []
    
    for line in lines:
        stripped = line.strip()
        
        # Bỏ dòng chỉ có ký tự table rác: |, +, -, =, khoảng trắng
        if re.fullmatch(r'[\|\+\-\=\s]*', stripped):
            continue
        
        # Bỏ dòng rác navigation
        if stripped in ("Về đầu trang",):
            continue
        
        cleaned.append(stripped)
    
    # Gộp nhiều dòng trắng liên tiếp thành 1
    result = re.sub(r'\n{3,}', '\n\n', "\n".join(cleaned))
    
    return result.strip()
if __name__ == "__main__":
    file_path = "/home/doduy/Downloads/data_cminh/Luât BHXH 07.doc"
    
    md_content = word_to_markdown(file_path)
    
    output_path = Path(file_path).with_suffix(".md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    
    print(f"Đã lưu: {output_path}")
    print(f"Nội dung:\n{md_content[:500]}...")