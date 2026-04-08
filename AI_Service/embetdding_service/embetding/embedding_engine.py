import os
import uuid 
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, PayloadSchemaType
from sentence_transformers import SentenceTransformer
from config.config import settings
client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
model = SentenceTransformer(settings.MODEL_QDRANT)

COLLECTION_NAME = "TEST"

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

def process_embedding_for_user(userid , group_id,base ,chuck):
    print(f"USER {userid}")
    print(f"USER {group_id}")
    print(f"USER {base}")
    print(f"USER {chuck}")


    