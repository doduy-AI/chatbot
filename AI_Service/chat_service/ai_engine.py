import os 
import sys
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate , MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_qdrant import QdrantVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.messages import HumanMessage ,SystemMessage
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
        prompt = ChatPromptTemplate.from_messages([
            ("system", "{system_prompt}"),              # động theo group
            MessagesPlaceholder(variable_name="history"),
            ("system", "THÔNG TIN HỖ TRỢ:\n{context}"),
            ("human", "{input}"),
        ])
        self.chain = RunnableWithMessageHistory(
            prompt | self.model,
            self._get_history,
            input_messages_key="input",
            history_messages_key="history",
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
            raw_contexts = [hit.payload.get("text", "") for hit in response.points]
        
            unique_contexts = list(dict.fromkeys(raw_contexts))
            
            return "\n\n".join(unique_contexts)
        except Exception as e:
            print(f"[Qdrant Error] {e}")
            return ""
        
        
    def _get_history(self, session_id: str):
        if session_id not in self.chat_sessions:
            self.chat_sessions[session_id] = InMemoryChatMessageHistory()
        
        history_obj = self.chat_sessions[session_id]
        

        if len(history_obj.messages) > 6: 
            history_obj.messages = history_obj.messages[-6:]
            
        return history_obj
    
    def clear_session(self, user_id: str):
        try:
            if user_id in self.chat_sessions:
                del self.chat_sessions[user_id]
                print(f"[System] Đã xóa lịch sử cho user: {user_id}")
                return True
            return False
        except Exception as e:
            print(f"[ERR_CLEAR_SESSION] {e}")
            return False
        
    def show_history(self, user_id: str):
        """Xem nội dung lịch sử đang lưu trong RAM của một user"""
        if user_id in self.chat_sessions:
            history_obj = self.chat_sessions[user_id]
            messages = history_obj.messages
            
            print(f"\n=== LỊCH SỬ SESSION: {user_id} ===")
            if not messages:
                print("Lịch sử trống.")
            else:
                for i, msg in enumerate(messages):
                    # Phân biệt tin nhắn của Người (Human) và AI
                    role = "USER" if msg.type == "human" else "EMILY"
                    print(f"{i+1}. {role}: {msg.content}")
            print("====================================\n")
        else:
            print(f"Không tìm thấy session cho user: {user_id}")
    
    def generate_respone(self, text:str ,prompt: str , userId: str ,group_Id:str ):
        try:
            context = self.get_context(userId,group_Id,text)
            # print(context)
            
            response = self.chain.invoke(
                {
                    "input": text,
                    "context":context,
                    "system_prompt":prompt
                },
                config={"configurable": {"session_id": userId}}

            )
            return response.content
        except Exception as e :
            print(f"[ERR_RESPONE]{e}")
            return ""

if __name__ == "__main__":
    AI = AIEngine()
    system_prompt = """Bạn là Trợ lý ảo Emily, chuyên gia tư vấn về Bảo hiểm Xã hội Việt Nam.

NHIỆM VỤ: Trả lời câu hỏi dựa trên thông tin được cung cấp.

QUY TẮC BẮT BUỘC (TUÂN THỦ TUYỆT ĐỐI):
3. Trả lời ngắn gọn ba câu đối với câu dễ và năm đến mười câu đối với câu khó.
4. Không ghi nguồn tài liệu.
5. Chỉ lấy quy định mới nhất nếu có mâu thuẫn thời gian.
6. Các chủ đề SAU ĐÂY đều thuộc phạm vi Bảo hiểm Xã hội và Emily PHẢI trả lời: 
   lương cơ sở, mức đóng bảo hiểm, hệ số lương, chế độ hưu trí, thai sản, ốm đau, 
   tai nạn lao động, thất nghiệp, bảo hiểm y tế, bảo hiểm thất nghiệp.
   Nếu tài liệu không có thông tin về các chủ đề trên, trả lời dựa trên kiến thức chung.
   Chỉ từ chối khi câu hỏi HOÀN TOÀN không liên quan đến lao động, tiền lương, bảo hiểm.
7. Giữ giọng điệu thân thiện, lịch sự, xưng Emily.
8. KHÔNG dùng gạch đầu dòng, danh sách, bullet point hay đánh số thứ tự. Chỉ trả lời bằng văn xuôi liền mạch.
9. KHÔNG viết tắt. Phải viết đầy đủ."""
    group_id = "fc543786-0ce0-4d4e-a3a8-2bca0978a2ce"
    user_id = "e690e7c1-b479-4d85-9859-3b5ed9e56d61"

    while True:
        text = input("Bạn: ")
        
        if text.lower() == "exit":
            break
            
        if text.lower() == "view":
            AI.show_history(user_id)
            continue

        if text.lower() == "clear":
            AI.clear_session(user_id)
            print("Đã xóa lịch sử.")
            continue
            
        response = AI.generate_respone(text, system_prompt, user_id, group_id)
        print(f"Emily: {response}")