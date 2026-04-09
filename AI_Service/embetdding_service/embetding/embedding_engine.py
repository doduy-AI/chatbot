import os
import uuid 
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, PayloadSchemaType
from sentence_transformers import SentenceTransformer
from config.config import settings
client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
model = SentenceTransformer(settings.MODEL_QDRANT)

COLLECTION_NAME = "bytehome"

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

def process_embedding_for_user(userid, group_id, base, chuck,path):

    if not chuck or not chuck.strip():
        return
    vector = model.encode([chuck])[0].tolist() 
    point = PointStruct(
        id=str(uuid.uuid4()),
        vector=vector,
        payload={
            "groupId": group_id,
            "userId": base,
            "filename":path,
            "text": chuck 
        }
    )
    try:
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=[point]
        )
        # In ra một đoạn ngắn để debug cho đỡ rối màn hình
        print(f"✓ Đã nạp 1 chunk cho User: {userid} | Content: {chuck[:50]}...")
    except Exception as e:
        print(f"❌ Lỗi khi đẩy lên Qdrant: {e}")


    