from embetdding_service.embetding.embedding_engine import process_embedding_for_user as embetdding
from pathlib import Path
def chunk_text(folder_path_clean, u_id, groupId, base, chunk_size=600, overlap=50):
    folder = Path(folder_path_clean)
    
    for file_path in folder.iterdir():
        if not file_path.is_file():
            continue
            
        print(f"Đang chunk file: {file_path.name}")
        
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        
        words = text.split()
        i = 0
        count = 0
        
        while i < len(words):
            chunk = " ".join(words[i:i + chunk_size])
            embetdding(u_id, groupId, base, chunk, file_path.name)
            i += chunk_size - overlap
            count += 1
        
        print(f"✓ File {file_path.name}: {count} chunks")