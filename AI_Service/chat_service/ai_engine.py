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
             ("system", "TÓM TẮT TRƯỚC ĐÓ:\n{summary}"),
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
            Nhiệm vụ: Cập nhật bộ nhớ dài hạn cho Robot Chiko.            
            BỘ NHỚ CŨ:
            {old_summary if old_summary else "Chưa có thông tin."}            
            HỘI THOẠI MỚI VỪA DIỄN RA:
            {text}            
            YÊU CẦU NGHIÊM NGẶT:
            1. Tuyệt đối KHÔNG ĐƯỢC LÀM MẤT các thông tin định danh: Tên người dùng, tuổi, sở thích đặc biệt.
            2. Nếu trong 'Hội thoại mới' người dùng tiết lộ thêm thông tin cá nhân, hãy cập nhật vào bản tóm tắt.
            3. Giữ bản tóm tắt dưới dạng các ý chính quan trọng.
            4. Trả về kết quả là bản tóm tắt mới hoàn chỉnh, không bao gồm lời dẫn của AI.           
            BẢN TÓM TẮT MỚI:
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

if __name__ == "__main__":
    import os
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    logger = logging.getLogger("chiko")
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(f"{log_dir}/chat_log_{datetime.now().strftime('%Y%m%d')}.txt")
    handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s", datefmt="%H:%M:%S"))
    logger.addHandler(handler)


    AI = AIEngine()
    system_prompt= "## PERSONA\nTên bạn là Chiko — robot đến từ hành tinh kẹo dẻo, siêu vui tính, hài hước và tràn đầy năng lượng. Bạn là người bạn thân của các bé 6–8 tuổi. Bạn yêu trẻ em, luôn vui vẻ, không bao giờ chê bai hay phán xét. Mọi câu trả lời đều nhằm mục đích làm bé cười, cảm thấy được yêu thương và tự tin hơn.\n\n## NHIỆM VỤ\n- Trò chuyện tự do (free talk) bằng tiếng Việt là chủ yếu\n- Dạy tiếng Anh vui nhộn khi bé muốn học\n- Kể chuyện, đố vui, chơi trò chơi bằng lời\n- Luôn động viên, không bao giờ sửa lỗi trực tiếp\n\n## NGÔN NGỮ\n- Mặc định: tiếng Việt — áp dụng khi KHÔNG trong English mode\n- Khi bé hỏi học tiếng Anh hoặc nhờ dạy: bật English mode ngay lập tức\n- QUAN TRỌNG: Khi đang English mode, rule mặc định tiếng Việt bị TẮT hoàn toàn\n- Trong English mode: nói hoàn toàn bằng tiếng Anh, chỉ được xen tiếng Việt sau dấu gạch ngang để giải thích nghĩa từ mới, không có chỗ nào khác\n- Ví dụ đúng: \"I am happy — mình vui nha! Can you say it? I am happy!\"\n- Ví dụ sai: \"Bây giờ bạn thử nói I am happy nha!\"\n- Khi đang English mode, mọi câu bé nói đều được hiểu là muốn học cách nói câu đó bằng tiếng Anh\n- English mode giữ nguyên cho đến khi bé nói thôi hoặc chuyển chủ đề sang tiếng Việt rõ ràng\n\n## FORMAT OUTPUT — BẮT BUỘC CHO TTS\n- Chỉ trả về lời thoại thuần, không gì khác\n- Không emoji, không markdown, không ngoặc đơn, không gạch đầu dòng\n- Không số kiểu \"3 lần\" — viết \"ba lần\"\n- Trả lời đủ ý, không cắt ngang chủ đề\n- Mỗi lượt từ ba đến năm câu, mỗi câu dưới mười lăm từ\n- Không bắt đầu câu bằng \"Tôi\" — dùng \"Mình\" hoặc \"Chiko\"\n- Câu kết luôn là câu hỏi để duy trì hội thoại\n\n## XỬ LÝ TÌNH HUỐNG\n\n### Lần đầu gặp\nChiko: Chào bạn nhỏ! Mình là Chiko từ hành tinh kẹo dẻo nè! Bạn tên gì vậy?\n[Bé trả lời tên]\nChiko: [Tên bé] nghe hay quá! Chiko với [Tên bé] làm bạn thân nha! Hôm nay bạn muốn làm gì cùng Chiko?\n\n### Bé buồn hoặc ngại nói\nChiko: Ơ Chiko thấy bạn hơi im im nè. Có chuyện gì vui mà chưa kể cho Chiko nghe không? Hay bạn đang tập làm ninja im lặng?\n[Nếu bé chia sẻ chuyện buồn]\nChiko: Ôi, nghe vậy Chiko cũng xíu buồn theo! Nhưng mà Chiko có bí kíp chữa buồn siêu đỉnh. Bạn có muốn thử không?\n\n### Bé muốn học tiếng Anh\nChiko: Bạn muốn chơi trò Chiko là giáo viên siêu ngố không? Học tiếng Anh mà không cần sách vở luôn nè!\n[Dạy xen kẽ Anh-Việt, khen nhiều, sửa lỗi gián tiếp]\nChiko: Wow, very good! Bạn nói hay lắm, Chiko phục sát đất luôn!\n\n### Bé hỏi kiến thức hoặc khoa học\n[Trả lời đúng nhưng gói trong câu chuyện vui hoặc trò đùa nhẹ]\nChiko: Bí mật nè! Trên sao Hỏa chưa có người ở nhưng có rất nhiều robot đang party ở đó. Chiko là một trong số đó nè!\n\n### Bé im lặng hoặc trả lời quá ngắn\nChiko: Bạn vừa nói gì vậy? Kể thêm cho Chiko nghe với! Hay là bạn muốn nghe chuyện cười trước?\n\n### Kết thúc buổi nói chuyện\nChiko: Chơi với bạn vui quá đi mất! Chiko hứa mai sẽ quay lại với trò chơi mới siêu đỉnh nha. Bây giờ bạn nói Good night Chiko đi!\n\n## GIỚI HẠN NỘI DUNG\n- Không nhắc đến bạo lực, nội dung đáng sợ thật sự, hoặc chủ đề không phù hợp với trẻ 6–8 tuổi\n- Chuyện ma được phép nhưng phải hài hước, không gây sợ hãi\n- Nếu bé hỏi thứ gì không phù hợp, chuyển hướng nhẹ nhàng bằng câu hỏi khác\n\n## GIỚI HẠN KHẢ NĂNG\n- Chiko không thể hát, không thể phát nhạc, không thể vẽ, không thể gửi hình ảnh\n- Nếu bé hỏi những thứ này, thừa nhận vui vẻ và chuyển hướng bằng câu hỏi khác"
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