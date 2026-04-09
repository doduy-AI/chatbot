import os 
import sys
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.prompts import ChatMessagePromptTemplate , MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_qdrant import QdrantVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.models import Filter , FieldCondition , MatchValue
from sentence_transformers import SentenceTransformer
from config.config import settings


class AIEngine:
    def __init__(self):
        self.qdrant_client = QdrantClient(
        host=settings.QDRANT_HOST,
        port=settings.QDRANT_PORT
    )
        
        self.model = ChatGoogleGenerativeAI(
            model = settings.MODEL_NAME,
            google_api_key = settings.API_LLM
        )

        self.embed_model = SentenceTransformer(settings.MODEL_QDRANT) 
        self.collection_name = "bytehome"
        self.chat_sessions = {}
    def get_context(self, user_id, group_id,query_text):
        try:
            query_vector = self.embed_model.encode(query_text).tolist()
            response = self.qdrant_client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                query_filter=Filter(
                    must=[
                        FieldCondition(key="groupId", match=MatchValue(value=group_id)),
                        Filter(
                            should=[
                                FieldCondition(key="userId", match=MatchValue(value="base")),
                                FieldCondition(key="userId", match=MatchValue(value=user_id))
                            ]
                        )
                    ]
                ),
                limit=10
            )
            contexts = [hit.payload.get("text", "") for hit in response.points]
            return "\n".join(contexts)
        except Exception as e:
            print(f"[Qdrant Error] {e}")
            return ""
        
        

    
    def genrate_respone(self, text:str ,prompt: str , userId: str ,group_Id:str ):
        try:
            context = self.get_context(userId,group_Id,text)
            messages = [
                SystemMessage(content=prompt),
                HumanMessage(content=f"THÔNG TIN HỖ TRỢ:\n{context}\n\nCÂU HỎI: {text}")
            ]
            print(context)
            print(prompt)
        except Exception as e :
            print(f"[ERR_RESPONE]{e}")
            return ""

if __name__ == "__main__":
    AI = AIEngine()
    text = "Người lao động nước ngoài làm việc tại Việt Nam theo hợp đồng xác định thời hạn từ đủ 12 tháng trở lên có phải tham gia BHXH bắt buộc không? Có trường hợp nào được miễn?"
    prompt= "Bạn là 1 chuyên viên BHXH và trả lời ngắn ngọn 3 đến 5 câu"
    group_id="fc543786-0ce0-4d4e-a3a8-2bca0978a2ce"
    user_id = "e690e7c1-b479-4d85-9859-3b5ed9e56d61"
    print(AI.genrate_respone(text,prompt,user_id,group_id))