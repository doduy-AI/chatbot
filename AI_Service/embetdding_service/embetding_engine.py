import os
import uuid
import docx
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, PayloadSchemaType
from sentence_transformers import SentenceTransformer
from config.config import settings
client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
model = SentenceTransformer(settings.MODEL_QDRANT)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
COLLECTION_NAME = "customer_vectors"
UPLOAD_BASE_DIR = BASE_DIR / "uploads"

def init_storage():
    if not client.collection_exists(COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )
        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="userId",
            field_schema=PayloadSchemaType.KEYWORD,
        )
        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="groupId",
            field_schema=PayloadSchemaType.KEYWORD,
        )
        print(f" Đã khởi tạo thành công collection: {COLLECTION_NAME}")

init_storage()

def extract_text(file_path):
    ext = file_path.suffix.lower()
    try:
        if ext == ".txt":
            with open(file_path, "r", encoding="utf-8-sig") as f:
                return f.read()
        elif ext == ".docx":
            doc = docx.Document(file_path)
            return "\n".join([p.text for p in doc.paragraphs])
    except Exception as e:
        print(f" Lỗi đọc file {file_path.name}: {e}")
    return ""


def process_embedding_for_user(user_id ,group_id):
    user_dir = Path(UPLOAD_BASE_DIR) / user_id
    if not user_dir.exists():
        print("Thư mục {user_id} không tồn tại ")
        return
    all_points = []

    for file_path in user_dir.glob("*"):
        if file_path.suffix.lower() in [".txt", ".docx"]:
            print(f" Đang xử lý: {file_path.name}")
            content = extract_text(file_path)
            
            if not content.strip():
                continue

            chunks = [content[i:i+600] for i in range(0, len(content), 600)]
            
            vectors = model.encode(chunks).tolist()
            
            for idx, vector in enumerate(vectors):
                all_points.append(PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload={
                        "groupId": group_id,
                        "userId": user_id,
                        "fileName": file_path.name,
                        "text": chunks[idx]
                    }
                ))
    if all_points:
        client.upsert(collection_name=COLLECTION_NAME, points=all_points)
        print(f" Đã lưu {len(all_points)} đoạn văn cho User: {user_id}")
    else:
        print(f"ℹKhông có dữ liệu mới để cập nhật cho User: {user_id}")
