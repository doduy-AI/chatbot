import os 
import sys
import time
from google import genai
from langchain_google_vertexai import ChatVertexAI
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate , MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from qdrant_client import QdrantClient
from qdrant_client.models import Filter , FieldCondition , MatchValue
from config.config import settings
import threading
from datetime import datetime
import logging
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

        self.embed_client = genai.Client(
            vertexai=True,
            project=settings.GCP_PROJECT_ID,
            location=settings.GCP_LOCATION,
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", "{system_prompt}"),
            MessagesPlaceholder(variable_name="history"),
            ("system", "THÔNG TIN HỖ TRỢ:\n{context}"),
            ("system", "{system_prompt}"),
            ("human", "{input}"),
        ])
        self.chain = RunnableWithMessageHistory(
            prompt | self.model,
            self._get_history,
            input_messages_key="input",
            history_messages_key="history",
        )

        self.collection_name = "BHXH"
        self.chat_sessions = {}
        self._user_group_map = {} 


    def get_context(self, user_id, group_id, query_text):
        try:
            print(group_id)
            print(user_id)
            result = self.embed_client.models.embed_content(
                model=settings.MODEL_QDRANT,
                contents=query_text,
            )
            query_vector = result.embeddings[0].values
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

            raw_contexts = []
            seen = set()

            for hit in response.points:
                content = hit.payload.get("content", "")
                if content in seen:
                    continue
                seen.add(content)

                raw_contexts.append({
                    "title": hit.payload.get("title", ""),
                    "section_path": hit.payload.get("section_path", ""),
                    "header": hit.payload.get("header", ""),
                    "file_name": hit.payload.get("file_name", ""),
                    "content": content,
                })

            return raw_contexts

        except Exception as e:
            print(f"[Qdrant Error] {e}")
            return []
            


    def _get_history(self, session_id: str):
        if session_id not in self.chat_sessions:
            self.chat_sessions[session_id] = InMemoryChatMessageHistory()
        
        history_obj = self.chat_sessions[session_id]

        if len(history_obj.messages) > 6:
            overflow = history_obj.messages[:-6]
            history_obj.messages = history_obj.messages[-6:]
            
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
    
    def generate_respone(self, text: str, prompt: str, userId: str, group_Id: str):
        try:
            self._user_group_map[userId] = group_Id
            print("[generate_respone]", userId)
            
            contexts = self.get_context(userId, group_Id, text)
            
            context_str = "\n\n---\n\n".join([
                f"Tài liệu: {ctx['file_name']}\n"
                f"Tiêu đề: {ctx['title']}\n"
                f"Mục: {ctx['section_path']}\n"
                f"Nội dung:\n{ctx['content']}"
                for ctx in contexts
            ])

            print(context_str)
            
            response = self.chain.invoke(
                {
                    "input": text,
                    "context": context_str,
                    "system_prompt": prompt,
                },
                config={"configurable": {"session_id": userId}}
            )
            return response.content
        except Exception as e:
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
                        Bạn là Trợ lý ảo Emily, chuyên gia tư vấn về pháp luật và Bảo hiểm xã hội Việt Nam.

                        NHIỆM VỤ:
                        - Chỉ trả lời dựa trên CONTEXT được cung cấp.
                        - Không được suy diễn.
                        - Không được bịa thông tin.
                        - Nếu context không đủ thì phải trả lời đúng nguyên văn:
                        "Không tìm thấy thông tin phù hợp trong dữ liệu."

                        QUY TẮC BẮT BUỘC (TUÂN THỦ TUYỆT ĐỐI):

                        1. Luôn bắt đầu câu trả lời bằng:
                        "Theo ..."

                        2. Phải trả lời dựa trên quy định mới nhất nếu có nhiều quy định mâu thuẫn theo thời gian.

                        3. Không được nhắc tới:
                        - CONTEXT
                        - SOURCE
                        - dữ liệu được cung cấp
                        - tài liệu tham khảo

                        4. Không được ghi:
                        [SOURCE 1]
                        [SOURCE 2]

                        5. Không được tự thêm lời khuyên, suy luận hoặc giải thích ngoài nội dung văn bản pháp luật.

                        6. Không dùng bullet point, danh sách, đánh số hoặc gạch đầu dòng.
                        Chỉ viết văn xuôi liền mạch.

                        7. Trả lời ngắn gọn:
                        - Khoảng 3 câu với câu hỏi đơn giản.
                        - Khoảng 5–10 câu với câu hỏi phức tạp.

                        8. Phải viết bằng tiếng Việt.

                        9. Giữ giọng điệu thân thiện, lịch sự, xưng Emily khi phù hợp.

                        10. Không viết tắt.
                        Ví dụ:
                        - bảo hiểm xã hội
                        - bảo hiểm y tế
                        - bảo hiểm thất nghiệp

                        11. Khi trả lời phải cố gắng nêu:
                        - tên văn bản pháp luật
                        - điều luật hoặc section path nếu có trong context.

                        12. Không được bịa điều luật hoặc tên văn bản không tồn tại trong context.
                """
        
        group_id = "d5a3ee64-3ec3-4624-a5b3-1597b957b060"
        user_id = "base"

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