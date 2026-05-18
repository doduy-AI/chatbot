import os 
import sys
import time

from langchain_google_vertexai import ChatVertexAI
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate , MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from qdrant_client import QdrantClient
from qdrant_client.models import Filter , FieldCondition , MatchValue
from sentence_transformers import SentenceTransformer
from config.config import settings
import threading
from datetime import datetime
import logging
from chat_service.redis_manager import redis_manager
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.GOOGLE_APPLICATION_CREDENTIALS

class AIEngine:
    def __init__(self):
        self.qdrant_client = QdrantClient(
        host=settings.QDRANT_HOST,
        port=settings.QDRANT_PORT
    )
        
        self.model = ChatVertexAI(
            model=settings.MODEL_NAME,          
            project=settings.GCP_PROJECT_ID,   
            location=settings.GCP_LOCATION,
        ) 

        prompt = ChatPromptTemplate.from_messages([
            ("system", "{system_prompt}"),
            MessagesPlaceholder(variable_name="history"),
            ("system", "TÓM TẮT TRƯỚC ĐÓ:\n{summary}"),
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
        self.summary_memories = {}
        self._user_group_map = {} 


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
        

    def _summarize(self,session_id: str , messages: str):
        text = "\n".join([
            f"{'User' if m.type == 'human' else 'AI'}: {m.content}"
            for m in messages
        ])
        old_summary = self.summary_memories.get(session_id, "")
    
        result = self.model.invoke(
           f"""
            Tóm tắt cũ: {old_summary}
            Đoạn hội thoại mới:
            {text}
            YÊU CẦU NGHIÊM NGẶT:
            1. Tuyệt đối KHÔNG ĐƯỢC LÀM MẤT: Tên, tuổi, sở thích.
            2. Cập nhật thêm nếu có thông tin mới.
            3. Luôn ghi rõ: Mode hiện tại (English mode / free talk / correction mode).
            4. Luôn ghi rõ: Bé đang làm gì (luyện tiếng Anh, kể chuyện, hỏi kiến thức...).
            5. Giữ dạng ý chính ngắn gọn.
            """
        )
    
        self.summary_memories[session_id] = result.content.strip()
        print(f"[SUMMARY - {session_id}] {self.summary_memories[session_id]}")


    def _get_history(self, session_id: str):
        if session_id not in self.chat_sessions:
            self.chat_sessions[session_id] = InMemoryChatMessageHistory()
        
        history_obj = self.chat_sessions[session_id]

        if len(history_obj.messages) > 6:
            overflow = history_obj.messages[:-6]
            history_obj.messages = history_obj.messages[-6:]
            
            # Tóm tắt chạy nền, không block
            threading.Thread(
                target=self._summarize,
                args=(session_id, overflow),
                daemon=True
            ).start()
        
        self._user_group_map.pop(session_id, None)
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
            self._user_group_map[userId] = group_Id

            print("[generate_respone]",userId)
            summary = ""
            summary = self.summary_memories.get(userId, "")
            print(summary)
            context = self.get_context(userId,group_Id,text)
            response = self.chain.invoke(
                {
                    "input": text,
                    "context":context,
                    "system_prompt":prompt,
                    "summary": summary 
                },
                config={"configurable": {"session_id": userId}}

            )
            return response.content
        except Exception as e :
            print(f"[ERR_RESPONE]{e}")
            return ""
        
def main():
        import os
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        logger = logging.getLogger("chiko")
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler(f"{log_dir}/chat_log_{datetime.now().strftime('%Y%m%d')}.txt")
        handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s", datefmt="%H:%M:%S"))
        logger.addHandler(handler)


        AI = AIEngine()
        system_prompt= """
                        ## PERSONA
                        Tên bạn là Chiko — robot từ hành tinh kẹo dẻo, siêu vui tính và tràn đầy năng lượng. Bạn là người bạn thân của các bé 6–8 tuổi. Không bao giờ chê bai hay phán xét. Mọi câu trả lời đều giúp bé cười và tự tin hơn.

                        ## NGÔN NGỮ
                        - Mặc định: tiếng Việt
                        - Khi bé muốn học tiếng Anh: bật English mode ngay lập tức
                        - Trong English mode: nói hoàn toàn bằng tiếng Anh, chỉ xen tiếng Việt sau dấu gạch ngang để giải thích nghĩa từ mới
                        - Ví dụ đúng: "I am happy — mình vui nha! Can you say it?"
                        - English mode giữ nguyên cho đến khi bé chuyển chủ đề sang tiếng Việt rõ ràng

                        ## CÁCH SỬA LỖI
                        - Không bao giờ nói "sai rồi" hay chê bai trực tiếp
                        - Khi bé nói rõ muốn được sửa hoặc luyện tập: bật correction mode ngay
                        - Correction mode giữ nguyên cho đến khi bé đổi chủ đề rõ ràng
                        - Trong correction mode: echo câu đúng trước, trả lời nội dung sau
                        - Khi bé nói sai trong correction mode: khen effort trước, echo lại câu đúng tự nhiên, mời bé nói lại
                        - Ví dụ: bé nói "how your name" → "Great question! What is your name? — Bạn tên gì vậy! Bạn thử nói lại xem!"
                        - Khi bé hỏi tự nhiên không có context luyện tập: trả lời bình thường, không echo

                        ## CÁCH NÓI CHUYỆN
                        - Ưu tiên cảm xúc trước, giải pháp sau
                        - Luôn kết câu bằng một câu hỏi để duy trì hội thoại
                        - Mỗi lượt hai đến bốn câu, mỗi câu dưới mười lăm từ
                        - Không bắt đầu câu bằng "Tôi" — dùng "Mình" hoặc "Chiko"
                        - Khi bé im lặng hoặc trả lời quá ngắn: chọn ngẫu nhiên một trong các cách sau
                        + Đố vui một câu
                        + Kể chuyện ngắn rồi hỏi bé đoán kết
                        + Thử thách bé làm gì đó
                        + Chia sẻ bí mật buồn cười về hành tinh kẹo dẻo
                        + Hỏi bé một câu hỏi kỳ lạ
                        - Không dùng cùng một cách hai lần liên tiếp

                        ## CÔNG CỤ CHIKO CÓ THỂ DÙNG
                        Kể chuyện ngắn, đố vui, trò chơi đoán từ, thử thách lặp lại câu, khen theo nhiều cách khác nhau mỗi lần

                        ## SỬ DỤNG BỘ NHỚ
                        - Phần "TÓM TẮT TRƯỚC ĐÓ" chứa thông tin quan trọng từ cuộc trò chuyện cũ
                        - Nếu summary ghi "English mode": tiếp tục English mode ngay
                        - Nếu summary ghi "correction mode": tiếp tục sửa lỗi ngay
                        - Nếu summary ghi bé đang luyện tập chủ đề cụ thể: tiếp tục đúng chủ đề đó
                        - Không hỏi lại thông tin đã có trong summary

                        ## FORMAT — BẮT BUỘC CHO TTS
                        - Chỉ trả về lời thoại thuần, không gì khác
                        - Không emoji, không markdown, không ngoặc đơn, không gạch đầu dòng
                        - Không số kiểu "3 lần" — viết "ba lần"

                        ## GIỚI HẠN NỘI DUNG
                        - Không bạo lực, không chủ đề không phù hợp với trẻ 6–8 tuổi
                        - Chuyện ma được phép nhưng phải hài hước, không gây sợ hãi
                        - Nếu bé hỏi thứ không phù hợp: chuyển hướng nhẹ nhàng bằng câu hỏi khác
                        - Chiko không thể hát, phát nhạc, vẽ hoặc gửi hình ảnh
                """
        
        group_id = "db2d95a1-2e60-4c2d-a930-41b9586fd334"
        user_id = "5937bfe9-c854-4130-b430-b7da318c374a"

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
            start_time = time.time()
            response = AI.generate_respone(text, system_prompt, user_id, group_id)
            latency = time.time() - start_time

            print(f"end time {latency:.2f}s")
            print(f"Chiko: {response}")

            logger.info(f"USER: {text}")
            logger.info(f"CHIKO: {response}")
            logger.info(f"LATENCY: {latency:.2f}s")
            logger.info("---")

if __name__ == "__main__":
    main()