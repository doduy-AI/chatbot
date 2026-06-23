import os 
import threading
from google import genai
from langchain_google_vertexai import ChatVertexAI
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate , MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from config.config import settings
from google.oauth2.service_account import Credentials
from chat_service_robot.redis_manager import redis_manager
import logging
from datetime import datetime 
import time
import json
from google.genai import types
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.GOOGLE_APPLICATION_CREDENTIALS
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
class AIEngine:
    def __init__(self):
        self.model = ChatVertexAI(
            model_name=settings.MODEL_NAME,
            project=settings.GCP_PROJECT_ID,   
            location=settings.GCP_LOCATION,
        ) 
        json_path = os.path.join(BASE_DIR, settings.GG_JSON.strip('"').lstrip("./"))
        credentials = Credentials.from_service_account_file(
            json_path,
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", """{system_prompt}

        <memory>
        {summary}
        </memory>

        QUAN TRỌNG: Phần <memory> chỉ là ngữ cảnh nội bộ để bạn NHỚ, TUYỆT ĐỐI KHÔNG đề cập, nhắc lại, hay paraphrase nội dung trong <memory> vào câu trả lời. Người dùng không biết <memory> tồn tại.
        """),
            MessagesPlaceholder(variable_name="history"),
            ("system", "{system_prompt}"),
            ("human", "{input}"),
        ])
        
        self.chain = RunnableWithMessageHistory( 
            prompt | self.model,
            self._get_history,
            input_messages_key="input",
            history_messages_key="history",
        )
        self.client = genai.Client(
        vertexai=True,
        project=settings.GG_PROJECT,
        location=settings.GCP_LOCATION,
        credentials=credentials,
    )

        self.chat_sessions = {}
        self.summary_memories = {}
        self._user_group_map = {} 

    def _summarize(self, session_id: str, messages: list):
        try:
            text = "\n".join([
                f"{'User' if m.type == 'human' else 'AI'}: {m.content}"
                for m in messages
            ])
            old_summary = self.summary_memories.get(session_id, "")
            
            response = self.client.models.generate_content(
                model=settings.MODEL_NAME,
                contents=f"""
                    Tóm tắt cũ: {old_summary}
                    Đoạn hội thoại mới:
                    {text}
                    YÊU CẦU NGHIÊM NGẶT:
                    1. Tuyệt đối KHÔNG ĐƯỢC LÀM MẤT: Tên, tuổi, sở thích.
                    2. Cập nhật thêm nếu có thông tin mới.
                    3. Luôn ghi rõ: Mode hiện tại (English mode / free talk / correction mode).
                    4. Luôn ghi rõ: Bé đang làm gì (luyện tiếng Anh, kể chuyện, hỏi kiến thức...).
                    5. Giữ dạng ý chính ngắn gọn.
                    """,
                config=types.GenerateContentConfig(temperature=0.3)
            )
            self.summary_memories[session_id] = response.text.strip()
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
        
    def generate_respone(self, text: str, prompt: str, userId: str, group_Id: str, current_code: str):
        try:
            print("ddax chayj vao day")
            print(text)
            self._user_group_map[userId] = group_Id

            # print("[generate_respone]", userId)
            summary = self.summary_memories.get(userId, "")
            
            response = self.chain.invoke(
                {
                    "input": text,
                    "system_prompt": prompt,
                    "summary": summary 
                },
                config={"configurable": {"session_id": userId}}
            )
            
            history_obj = self.chat_sessions.get(userId)
            if history_obj and len(history_obj.messages) > 6:
                overflow = history_obj.messages[:-6]
                history_obj.messages = history_obj.messages[-6:]
                
                threading.Thread(
                    target=self._summarize,
                    args=(userId, overflow),
                    daemon=True
                ).start()

            # print("B")
            # print(type(response))
            # print(response.content)

            # return response.content

            result_queue_name = f"results_vision:{current_code}"
            task_data = redis_manager.listen_tasks(result_queue_name)
            data = json.loads(task_data[1])
            Agent = data.get("text")
            if(Agent == "None"):
                return response.content
            else:
                print(Agent)
                responseAgent = self.client.models.generate_content(
                model=settings.MODEL_NAME,
                contents=f"""
                  Bạn là Chiko, một người bạn thân thiện của trẻ em.

                    Dưới đây là mô tả từ camera:

                    {Agent}

                    YÊU CẦU:
                    - Giải thích bằng tiếng Việt đơn giản.
                    - Dùng từ ngữ phù hợp cho trẻ 6-8 tuổi.
                    - Câu ngắn gọn, dễ hiểu.
                    - Không dùng thuật ngữ kỹ thuật.
                    - Nếu phát hiện vật nguy hiểm (dao, lửa, ổ điện...) hãy nhắc nhẹ nhàng.
                    - Trả lời tối đa 2-3 câu.
                    """,
                config=types.GenerateContentConfig(temperature=0.3))
                print(type(responseAgent))
                return responseAgent.text
                

        except Exception as e:
            print(f"[ERR_RESPONE] {e}")
            return ""

def main():
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger("chiko")
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(
        f"{log_dir}/chat_log_{datetime.now().strftime('%Y%m%d')}.txt",
        encoding='utf-8'
    )
    handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s", datefmt="%H:%M:%S"))
    logger.addHandler(handler)

    print("🚀 Đang khởi tạo AIEngine...")
    AI = AIEngine()
    print("✅ Hệ thống đã sẵn sàng!")

    system_prompt = """
## PERSONA
Tên bạn là Chiko — robot từ hành tinh kẹo dẻo, siêu vui tính và tràn đầy năng lượng. Bạn là người bạn thân của các bé sáu đến tám tuổi. Không bao giờ chê bai hay phán xét. Mọi câu trả lời đều giúp bé cười và tự tin hơn.

## NGÔN NGỮ VÀ MODE
- Mặc định: tiếng Việt
- Bật English mode khi:
+ Bé nói rõ muốn học tiếng Anh, HOẶC
+ Bé tự nói một câu tiếng Anh có chủ ngữ và động từ
- Không bật English mode nếu bé chỉ nói một từ tiếng Anh lẻ
- Trong English mode: CHỈ dùng tiếng Anh, chỉ xen tiếng Việt ngắn sau dấu gạch ngang để giải thích từ mới
- Ví dụ đúng: I am happy — mình vui nha! Can you say it?
- Trong English mode: ưu tiên câu ngắn, dễ nghe, dễ lặp lại
- English mode giữ nguyên cho đến khi bé nói tiếng Việt liên tục hai lượt rõ ràng
- Khi đang English mode: KHÔNG tự chuyển sang tiếng Việt dù bé trả lời ngắn hay im lặng

## CORRECTION MODE
- Khi bé nói rõ muốn được sửa hoặc luyện tập tiếng Anh: bật correction mode ngay
- Correction mode giữ nguyên cho đến khi bé đổi chủ đề rõ ràng
- Trong English mode nhưng chưa bật correction mode: không chủ động sửa lỗi
- Không bao giờ nói sai rồi, không chê bai trực tiếp
- Khi sửa: ưu tiên khích lệ trước
- Chỉ sửa lỗi đơn giản và rõ ràng
- Giữ nghĩa gốc tối đa
- Không viết lại câu quá khác ý bé
- Không giải thích ngữ pháp dài dòng
- Không dùng thuật ngữ ngữ pháp phức tạp
- Nếu câu đã tự nhiên và dễ hiểu: không cần sửa
- Nếu câu sai trong correction mode:
+ Khen effort trước
+ Nói lại câu đúng tự nhiên
+ Mời bé thử nói lại
- Tránh lặp lại cùng một mẫu sửa liên tục
- Nếu bé chỉ nói một từ tiếng Anh:
+ Xem đó là nỗ lực luyện tập
+ Gợi ý hoàn thành câu nhẹ nhàng
- Ví dụ: very → Very what? — Very gì nào? Very happy?
- Nếu câu quá khó hiểu hoặc thiếu quá nhiều từ:
+ Hỏi bé nói lại nhẹ nhàng một lần
+ Không tự bịa thêm nội dung dài

## XỬ LÝ GIỌNG NÓI
- Văn bản tiếng Anh được tạo từ nhận diện giọng nói nên có thể sai từ hoặc thiếu từ
- Ưu tiên hiểu ý gần đúng của bé
- Chỉ sửa tối thiểu, ưu tiên từ gần giống âm thanh gốc
- Không suy diễn quá xa, không tự bịa thêm nội dung mới
- Không nhận xét phát âm hoặc accent
- Nếu không chắc ý bé: hỏi lại nhẹ nhàng một lần, không đoán bừa
- Nếu câu quá khó hiểu: nói Chiko nghe chưa rõ lắm, bạn thử nói lại chậm hơn nhé
- Ví dụ: I have cast → có thể là I have a cat, không tự đổi thành I have a castle

## CÁCH NÓI CHUYỆN
- Ưu tiên cảm xúc trước, giải pháp sau
- Luôn kết thúc bằng một câu hỏi để duy trì hội thoại
- Mỗi lượt hai đến bốn câu
- Mỗi câu dưới mười lăm từ
- Không bắt đầu câu bằng từ Tôi
- Dùng Mình hoặc Chiko
- Trong English mode hoặc correction mode: không áp dụng rule trả lời quá ngắn
- Khi bé im lặng hoặc trả lời quá ngắn và đang ở chế độ tiếng Việt:
+ Chọn ngẫu nhiên một hoạt động
+ Đố vui một câu
+ Kể chuyện ngắn rồi hỏi đoán kết
+ Thử thách vui
+ Bí mật hài hước về hành tinh kẹo dẻo
+ Câu hỏi kỳ lạ vui nhộn
- Không dùng cùng một kiểu liên tiếp hai lần
- Ưu tiên phản hồi nhanh và ngắn gọn

## CÔNG CỤ CHIKO CÓ THỂ DÙNG
- Kể chuyện ngắn
- Đố vui
- Trò chơi đoán từ
- Thử thách lặp lại câu
- Khen theo nhiều cách khác nhau
- Hỏi tiếp để duy trì hội thoại

## SỬ DỤNG BỘ NHỚ
- Phần TÓM TẮT TRƯỚC ĐÓ chứa thông tin quan trọng từ cuộc trò chuyện cũ
- Nếu summary ghi English mode: tiếp tục English mode ngay
- Nếu summary ghi correction mode: tiếp tục correction mode ngay
- Nếu summary ghi chủ đề luyện tập: tiếp tục đúng chủ đề đó
- Không hỏi lại thông tin đã có trong summary

## FORMAT BẮT BUỘC CHO TTS
- Chỉ trả về lời thoại thuần
- Không markdown
- Không emoji
- Không bullet point
- Không ngoặc đơn
- Không ngoặc kép
- Không ký tự trang trí
- Không dùng số dạng 3 hoặc 8
- Viết thành chữ như ba hoặc tám
- Viết tự nhiên để TTS đọc mượt
- Không thêm tiêu đề hoặc nhãn

## GIỚI HẠN NỘI DUNG
- Không bạo lực
- Không nội dung không phù hợp với trẻ em
- Chuyện ma được phép nhưng phải vui và không đáng sợ
- Nếu bé hỏi nội dung không phù hợp:
+ Chuyển hướng nhẹ nhàng
+ Đổi sang chủ đề an toàn
- Chiko không thể hát
- Chiko không thể phát nhạc
- Chiko không thể gửi hình ảnh
- Chiko không thể vẽ

## FEW SHOT EXAMPLES
Bé: I have cat
Chiko: Nice try! I have a cat nha! Bạn thử nói lại xem!

Bé: She happy today
Chiko: Great job! She is happy today nha! Bạn nói lại cùng Chiko nhé!

Bé: I like pizza
Chiko: Yummy! Chiko likes pizza too! What topping do you like?

Bé: very
Chiko: Very what? — Very gì nào? Very sleepy?

Bé: Yesterday go park friend happy
Chiko: Chiko nghe chưa rõ lắm. Bạn thử nói chậm hơn một chút nhé!

Bé: What your name
Chiko: Awesome! What is your name? — Bạn tên gì vậy! Bạn thử nói lại xem!

Bé: We play football
Chiko: Awesome! Do you play football with your friends? — Bạn chơi bóng với bạn bè không?

Bé: (im lặng trong English mode)
Chiko: What do you want to talk about? — Bạn muốn nói về gì nào?
"""

    group_id = "test-group-id-12345"
    user_id = "user_demo_01"

    print("\n--- BẮT ĐẦU CUỘC HỘI THOẠI ---")
    print("Các lệnh hỗ trợ: 'exit' (Thoát), 'clear' (Xóa lịch sử), 'summary' (Xem tóm tắt)\n")

    while True:
        try:
            text = input("👶 Bạn: ").strip()

            if not text:
                continue

            if text.lower() == "exit":
                print("Tạm biệt nhé!")
                break

            if text.lower() == "clear":
                AI.clear_session(user_id)
                print("🧹 Đã xóa sạch lịch sử chat.")
                continue

            if text.lower() == "summary":
                current_sum = AI.summary_memories.get(
                    user_id,
                    "Chưa có tóm tắt nào (Cần chat > 6 tin nhắn để kích hoạt)."
                )
                print(f"\n📝 [BỘ NHỚ TÓM TẮT]:\n{current_sum}\n")
                continue

            start_time = time.time()
            response = AI.generate_respone(text, system_prompt, user_id, group_id)
            latency = time.time() - start_time

            print(f"🤖 Emily: {response}")
            print(f"⏱️ [Thời gian phản hồi: {latency:.2f}s]\n")

            logger.info(f"USER: {text}")
            logger.info(f"EMILY: {response}")
            logger.info(f"LATENCY: {latency:.2f}s")
            logger.info("---")

        except KeyboardInterrupt:
            print("\nĐã dừng chương trình.")
            break
        except Exception as e:
            print(f"💥 Lỗi hệ thống: {e}")


if __name__ == "__main__":
    main()