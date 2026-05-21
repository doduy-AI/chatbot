import os 
import threading
from langchain_google_vertexai import ChatVertexAI
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate , MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from config.config import settings

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.GOOGLE_APPLICATION_CREDENTIALS

class AIEngine:
    def __init__(self):
        # 1. SỬA CHÍNH XÁC THAM SỐ model_name
        self.model = ChatVertexAI(
            model_name=settings.MODEL_NAME, # Đổi từ model -> model_name         
            project=settings.GCP_PROJECT_ID,   
            location=settings.GCP_LOCATION,
        ) 

 
        prompt = ChatPromptTemplate.from_messages([
            ("system", "{system_prompt}"),
            MessagesPlaceholder(variable_name="history"),
            ("system", "TÓM TẮT TRƯỚC ĐÓ:\n{summary}"),
            ("system", "Không Được Phép Nhắc lại tóm tắt "),
            ("system", "{system_prompt}"),
            ("human", "{input}"),
        ])
        
        self.chain = RunnableWithMessageHistory( 
            prompt | self.model,
            self._get_history,
            input_messages_key="input",
            history_messages_key="history",
        )

        self.chat_sessions = {}
        self.summary_memories = {}
        self._user_group_map = {} 

    def _summarize(self, session_id: str , messages: list):
        """Hàm tóm tắt chạy độc lập hoàn toàn"""
        try:
            text = "\n".join([
                f"{'User' if m.type == 'human' else 'AI'}: {m.content}"
                for m in messages
            ])
            old_summary = self.summary_memories.get(session_id, "")
        
            # Sử dụng trực tiếp model chính để sinh tóm tắt
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
            # print(f"[SUMMARY - {session_id}] {self.summary_memories[session_id]}")
        except Exception as e:
            print(f"[ERR_SUMMARIZE] {e}")

    def _get_history(self, session_id: str):
        if session_id not in self.chat_sessions:
            self.chat_sessions[session_id] = InMemoryChatMessageHistory()
        return self.chat_sessions[session_id]
    
    def clear_session(self, user_id: str):
        try:
            if user_id in self.chat_sessions:
                del self.chat_sessions[user_id]
                if user_id in self.summary_memories:
                    del self.summary_memories[user_id]
                print(f"[System] Đã xóa lịch sử cho user: {user_id}")
                return True
            return False
        except Exception as e:
            print(f"[ERR_CLEAR_SESSION] {e}")
            return False
        
    def generate_respone(self, text: str, prompt: str, userId: str, group_Id: str):
        try:
            self._user_group_map[userId] = group_Id

            print("[generate_respone]", userId)
            summary = self.summary_memories.get(userId, "")
            
            # Thực thi chuỗi xích gọi Gemini lấy phản hồi chính
            response = self.chain.invoke(
                {
                    "input": text,
                    "system_prompt": prompt,
                    "summary": summary 
                },
                config={"configurable": {"session_id": userId}}
            )
            
            # 2. XỬ LÝ CẮT LỊCH SỬ VÀ TÓM TẮT TẠI ĐÂY (Sau khi luồng chính đã invoke xong)
            history_obj = self.chat_sessions.get(userId)
            if history_obj and len(history_obj.messages) > 6:
                overflow = history_obj.messages[:-6]
                history_obj.messages = history_obj.messages[-6:]
                
                # Kích hoạt luồng chạy nền tóm tắt an toàn, không block luồng trả về văn bản
                threading.Thread(
                    target=self._summarize,
                    args=(userId, overflow),
                    daemon=True
                ).start()

            return response.content
        except Exception as e:
            print(f"[ERR_RESPONE] {e}")
            return ""
