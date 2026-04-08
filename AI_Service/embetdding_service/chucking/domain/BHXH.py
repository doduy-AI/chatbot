import re
from .base import chunk_by_paragraph ,chunk_by_sentence
import os
from embetdding_service.embetding.embedding_engine import process_embedding_for_user as embedding
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
            if not part: continue
            
            # Nếu Điều luật không quá dài (dưới 2000 ký tự), ĐỪNG CẮT NỮA. 
            # Giữ nguyên cả Điều để AI hiểu trọn vẹn ngữ cảnh.
            if len(part) < 2000: 
                chunks.append(part)
            else:
                # Nếu bắt buộc phải cắt, hãy dùng overlap cao (ví dụ 200)
                chunks.extend(chunk_by_sentence(part, chunk_size=800, overlap=200))
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
    def __init__(self, folder_path: str,u_id: str, groupId: str, base: str):
        self.folder_path = folder_path
        self.final_results = []
        self.total_chunks = 0
        self.u_id = u_id
        self.groupId = groupId
        self.base = base
        self.process_folder()

    def process_folder(self):
        if not os.path.exists(self.folder_path):
            print("[CHUKING] forder không tồn tại ")
            return
        for filename in os.listdir(self.folder_path):
            path = os.path.join(self.folder_path, filename)
            if os.path.isfile(path):
                with open(path,'r',encoding='utf-8') as f :
                    content = f.read()
                    chunks =  chunk_luat(content)
                    if isinstance(chunks, list):
                        num_chunks = len(chunks)
                        self.total_chunks += num_chunks 
                        print(f"File {filename}: có {num_chunks} chunks")
                        userIdBase = "base" if self.base == 'yes' else self.user_id

                        for individual_chunk in chunks:
                            embedding(self.u_id,self.groupId, userIdBase, individual_chunk)
                    else:
                        # Nếu chunk_luat trả về kết quả khác list, xử lý tùy trường hợp
                        self.total_chunks += 1
            else:
                print(f"[ERR] Đường dẫn {path} không phải là 1 file ")
            print(path)

        print("đã vào đến đây",self.folder_path)
