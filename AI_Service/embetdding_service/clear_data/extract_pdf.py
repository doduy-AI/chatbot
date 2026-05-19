import pymupdf4llm
from pathlib import Path
from llama_parse import LlamaParse
from config.config import settings
from embetdding_service.redis_manager import redis_manager
from datetime import datetime

OCR_KEY = [
    settings.OCR1,
    settings.OCR2,
    settings.OCR3,
    settings.OCR4,
    settings.OCR5,
    settings.OCR6
]


def seconds_until_end_to_month() -> int:
    now = datetime.now()
    if now.month == 12:
        next_month = datetime(now.year + 1, 1, 1)
    else:
        next_month = datetime(now.year, now.month + 1, 1)
    return int((next_month - now).total_seconds())

def ban_key(index:int):
    ttl = seconds_until_end_to_month()
    redis_manager.client.setex(f"key_banned:{index}",ttl,"1")
    print(f"  Key {index + 1} hết quota, tự động mở lại đầu tháng sau")


def get_available_key() -> tuple[int, str] | None:
    for i, key in enumerate(OCR_KEY):
        if not redis_manager.client.get(f"key_banned:{i}"):
            return i, key
    return None

def pdf_word_to_markdown(filepath: str) -> str:
    try:
        md_conten = pymupdf4llm.to_markdown(filepath)
        return md_conten
    except Exception as e : 
        print("lỗi đọc", filepath)
        return ""


def pdf_scan_to_markdown(filepath: str) -> str:
    while True:
        result = get_available_key()

        if not result:
            print(" Tất cả API Key đều đã hết hạn hoặc bị chặn!")
            return ""
            
        index, key = result

        try:
            # print(f"Dùng key {index + 1} ...")
            parser = LlamaParse(
                api_key=key,
                result_type="markdown",
                language="vi",
                use_vendor_multimodal_model=True,
                vendor_multimodal_model_name="openai-gpt4o"
            )
            documents = parser.load_data(filepath)
            
            # Kiểm tra nếu documents rỗng
            if not documents:
                print(f"Key {index + 1} trả về dữ liệu rỗng.")
                ban_key(index)
                continue

            md_content = "\n\n".join([doc.text for doc in documents])          
            return md_content 

        except Exception as e:
            print(f"  ❌ Key {index + 1} gặp lỗi: {e}")
            ban_key(index)
            continue


if __name__ == "__main__":
    file_path = "/home/doduy/Downloads/1.22 Trả lời Hải Phòng (vợ chết, lấy vợ 2 thì bố mẹ vợ 1 không được hưởng tuất tháng).pdf"
    
    md_content = pdf_word_to_markdown(file_path)
    
    output_path = Path(file_path).with_suffix(".md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"Đã lưu: {output_path}")
