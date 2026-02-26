from google import genai
import sys , os
from qdrant_client import QdrantClient

from qdrant_client.models import Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config.config import settings


class AIEngine:
    def __init__(self):
        self.client = genai.Client(api_key=settings.API_LLM)
        self.qdrant_client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
        self.embed_model = SentenceTransformer(settings.MODEL_QDRANT)
        self.collection_name = "customer_vectors"
        print(type(settings.QDRANT_HOST))
        print(type(settings.QDRANT_PORT))
        print(f"Các phương thức đang có: {dir(self.qdrant_client)}")

    def get_context(self, user_id, query_text):
        try:
            # 1. Tạo vector từ query text
            query_vector = self.embed_model.encode(query_text).tolist()

            # 2. Sử dụng query_points thay vì query hoặc search
            # Trong bản FastEmbed, query_points nhận tham số 'query' là vector
            response = self.qdrant_client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                query_filter=Filter(
                    must=[
                        FieldCondition(key="userId", match=MatchValue(value=user_id))
                    ]
                ),
                limit=3
            )
            
            # 3. Lấy kết quả (Lưu ý: query_points trả về một object có thuộc tính .points)
            search_results = response.points
            
            contexts = [hit.payload.get("text", "") for hit in search_results]
            return "\n".join(contexts)
            
        except Exception as e:
            print(f"[Qdrant Error] {e}")
            return ""

    def generate_respone(self , prompt: str , uuid : str):
            try:
            #     response = self.client.models.generate_content(
            #     model=settings.MODEL_NAME,
            #     contents=prompt
            # )
                context = self.get_context(uuid, prompt)
                # return response.text
                return context
            except Exception as e :
                print(f"[genAI ERROR] {e}")
                return "[genAI] {e}"
if __name__ == "__main__":
    ai = AIEngine()
    result = ai.generate_respone("hôm nay là ngày bao nhiêu")
    print(result)