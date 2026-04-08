import re
from .base import chunk_by_paragraph ,chunk_by_sentence


def detect_luat_type(text: str) -> str:
    if re.search(r'Điều\s+\d+', text):
        return "dieu"
    elif re.search(r'^\d+\.\s+', text, re.MULTILINE):
        return "danh_sach"
    elif re.search(r'\|.*\|', text):
        return "bang"
    else:
        return "cong_van"
    

def chunk_luat(text: str, chunk_size=500, overlap=100) -> list[str]:
    van_ban_type = detect_luat_type(text)
    print(f"  Loại văn bản BHXH: {van_ban_type}")
    
    if van_ban_type == "dieu":
        pattern = r'(?=Điều\s+\d+)'
        parts = re.split(pattern, text)
        chunks = []
        for part in parts:
            part = part.strip()
            if not part:
                continue
            if len(part) > chunk_size * 2:
                chunks.extend(chunk_by_sentence(part, chunk_size, overlap))
            else:
                chunks.append(part)
        return chunks
    
    elif van_ban_type == "danh_sach":
        pattern = r'(?=^\d+\.\s+)'
        parts = re.split(pattern, text, flags=re.MULTILINE)
        return [p.strip() for p in parts if p.strip()]
    
    elif van_ban_type == "bang":
        return chunk_by_paragraph(text, chunk_size, overlap)
    
    else:  # cong_van
        return chunk_by_paragraph(text, chunk_size, overlap)


class BHXH:
    def __init__(self, folder_path: str):
        self.folder_path = folder_path
        self.final_results = []
        self.process_folder()

    def process_folder(self):
        print(self.folder_path)
