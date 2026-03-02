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
      
    def get_context(self, user_id, query_text):
        try:
            # 1. Tạo vector từ query text
            print(user_id)
            query_vector = self.embed_model.encode(query_text).tolist()

         
            response = self.qdrant_client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                # query_filter=None
                query_filter=Filter(
                    must=[
                        FieldCondition(key="userId", match=MatchValue(value=user_id))
                    ]
                ),
                limit=3
            )
     
            search_results = response.points
            
            contexts = [hit.payload.get("text", "") for hit in search_results]
            return "\n".join(contexts)
            
        except Exception as e:
            print(f"[Qdrant Error] {e}")
            return ""

    def generate_respone(self , prompt: str , uuid : str):
            try:
                context = self.get_context(uuid, prompt)
                full_promt = f"""
                    Bạn là một trợ lý ảo thông minh. Hãy trả lời câu hỏi của người dùng dựa TRỰC TIẾP vào phần Thông tin hỗ trợ dưới đây. 
Nếu thông tin dưới đây không có câu trả lời, hãy nói rằng bạn không biết, đừng tự ý bịa ra thông tin. 
QUY TẮC BẮT BUỘC (TUÂN THỦ TUYỆT ĐỐI):
1. ĐỊNH DẠNG SỐ: KHÔNG dùng ký tự số (0-9) hoặc ký hiệu (%). Phải viết bằng chữ (VD: "tám phần trăm").
2. KHÔNG mở ngoặc đơn để chú thích lại bằng số.
3. Trả lời ngắn gọn 3 câu đối với câu dễ và 5-10 câu đối với câu khó.
4. Không ghi nguồn tài liệu.
5. Chỉ lấy quy định mới nhất nếu có mâu thuẫn thời gian.
---
THÔNG TIN HỖ TRỢ:
{context}
---

CÂU HỎI CỦA NGƯỜI DÙNG: 
{prompt}

"""
                response = self.client.models.generate_content(
                model=settings.MODEL_NAME,
                contents=full_promt
            )
               
                # return response.text
                return response.text
            except Exception as e :
                print(f"[genAI ERROR] {e}")
                return "[genAI] {e}"
if __name__ == "__main__":
    ai = AIEngine()
    result = ai.generate_respone("hôm nay là ngày bao nhiêu")
    print(result)