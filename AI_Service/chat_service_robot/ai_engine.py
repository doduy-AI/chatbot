import os 
import threading
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate , MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from config.config import settings
import logging
from datetime import datetime 
import time
from google import genai
from google.genai import types
import json 

class AIEngine:
    def __init__(self):
        api_key = settings.GOOGLE_API_KEY

        if hasattr(api_key, "get_secret_value"):
            api_key = api_key.get_secret_value()

        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY chưa được cấu hình")

        self.model = ChatGoogleGenerativeAI(
            model=settings.MODEL_NAME,
            api_key=api_key,
            vertexai=False,
            temperature=0.7,
            max_retries=2,
            timeout=30,
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", """{system_prompt}

        <internal_context>
        {summary}
        </internal_context>

        NỘI QUY TUYỆT ĐỐI:
        - internal_context chỉ để hiểu ngữ cảnh.
        - Không bao giờ nói: tóm tắt, memory, bộ nhớ, ngữ cảnh nội bộ.
        - Không bao giờ giải thích rằng bạn đang dùng internal_context.
        - Chỉ trả lời trực tiếp như đang nói với người dùng .
        """),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}"),
        ])
        
        self.chain = RunnableWithMessageHistory( 
            prompt | self.model,
            self._get_history,
            input_messages_key="input",
            history_messages_key="history",
        ) 
        self.client = genai.Client(
            api_key=api_key
        )

        self.chat_sessions = {}
        self.summary_memories = {}
        self._user_group_map = {} 

    def _default_summary(self):
        return {
            "language_mode": "vi",
            "correction_mode": False,
            "current_activity": "free_talk",
            "child_profile": {
                "name": None,
                "age": None,
                "interests": []
            },
            "recent_topic": "",
            "important_facts": [],
            "last_user_intent": "",
            "do_not_reveal": True
        }

    def _normalize_summary(self, data: dict):
        default = self._default_summary()

        language_mode = data.get("language_mode", default["language_mode"])
        if language_mode not in ["vi", "en"]:
            language_mode = "vi"

        current_activity = data.get("current_activity", default["current_activity"])
        allowed_activities = [
            "free_talk",
            "english_practice",
            "correction_practice",
            "story",
            "quiz",
            "unknown"
        ]
        if current_activity not in allowed_activities:
            current_activity = "unknown"

        profile = data.get("child_profile") or {}

        return {
            "language_mode": language_mode,
            "correction_mode": bool(data.get("correction_mode", False)),
            "current_activity": current_activity,
            "child_profile": {
                "name": profile.get("name"),
                "age": profile.get("age"),
                "interests": profile.get("interests", [])
                    if isinstance(profile.get("interests", []), list)
                    else []
            },
            "recent_topic": data.get("recent_topic", ""),
            "important_facts": data.get("important_facts", [])
                if isinstance(data.get("important_facts", []), list)
                else [],
            "last_user_intent": data.get("last_user_intent", ""),
            "do_not_reveal": True
        }

    def _summarize(self, session_id: str, messages: list):
        try:
            text = "\n".join([
                f"{'User' if m.type == 'human' else 'AI'}: {m.content}"
                for m in messages
            ])

            old_summary = self.summary_memories.get(
                session_id,
                self._default_summary()
            )

            response = self.client.models.generate_content(
                model=settings.MODEL_NAME,
                contents=f"""
                            Bạn là bộ máy cập nhật state hội thoại nội bộ.

                            Nhiệm vụ:
                            - Đọc summary cũ.
                            - Đọc đoạn hội thoại mới.
                            - Trả về JSON hợp lệ duy nhất.
                            - Không viết giải thích.
                            - Không dùng markdown.
                            - Không viết câu "phần tóm tắt là".
                            - Không thêm text ngoài JSON.

                            Schema bắt buộc:
                            {{
                            "language_mode": "vi | en",
                            "correction_mode": true,
                            "current_activity": "free_talk | english_practice | correction_practice | story | quiz | unknown",
                            "child_profile": {{
                                "name": null,
                                "age": null,
                                "interests": []
                            }},
                            "recent_topic": "",
                            "important_facts": [],
                            "last_user_intent": "",
                            "do_not_reveal": true
                            }}

                            Quy tắc:
                            - Giữ lại tên, tuổi, sở thích nếu đã biết.
                            - Không tự bịa thông tin.
                            - Nếu không chắc thì để null hoặc unknown.
                            - language_mode chỉ là vi hoặc en.
                            - correction_mode là true hoặc false.
                            - important_facts chỉ lưu thông tin hữu ích, an toàn cho trẻ em.
                            - Không lưu địa chỉ, số điện thoại, trường học, thông tin nhạy cảm.

                            Summary cũ:
                            {json.dumps(old_summary, ensure_ascii=False)}

                            Đoạn hội thoại mới:
                            {text}
                        """,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    response_mime_type="application/json"
                )
            )

            new_summary = json.loads(response.text)
            new_summary = self._normalize_summary(new_summary)
            self.summary_memories[session_id] = new_summary

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
        
    def clean_response(self, text: str) -> str:
        banned = [
            "phần tóm tắt",
            "tóm tắt là",
            "tóm tắt trước đó",
            "summary",
            "memory",
            "bộ nhớ",
            "internal_context",
            "ngữ cảnh nội bộ"
        ]

        lower = text.lower()
        if any(x in lower for x in banned):
            return "Chiko hơi lộn xộn rồi. Mình chơi tiếp nhé, bạn muốn kể gì nào?"

        return text.strip()

    def generate_respone(self, text: str, prompt: str, userId: str, group_Id: str):
        try:
            self._user_group_map[userId] = group_Id

            # print("[generate_respone]", userId)
            summary = self.summary_memories.get(userId, self._default_summary())

            summary_text = json.dumps(
                summary,
                ensure_ascii=False,
                indent=2
            )
            
            response = self.chain.invoke(
                {
                    "input": text,
                    "system_prompt": prompt,
                    "summary": summary_text
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

            return self.clean_response(response.content)
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
            - Thường kết thúc bằng một câu hỏi tự nhiên.
            - Không đặt câu hỏi khi nó làm câu trả lời bị gượng ép.
            - Không dùng câu hỏi để kéo bé trở lại chủ đề cũ.
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
            + Câu hỏi kỳ lạ vui nhộn
            - Không dùng cùng một kiểu liên tiếp hai lần
            - Ưu tiên phản hồi nhanh và ngắn gọn

            ## THỨ TỰ ƯU TIÊN NGỮ CẢNH
            - Ý định trong câu hiện tại của bé luôn có ưu tiên cao nhất.
            - Chỉ tiếp tục hoạt động trước khi câu hiện tại liên quan đến hoạt động đó.
            - Nếu bé hỏi sang chủ đề mới, trả lời hoàn toàn theo chủ đề mới.
            - Không tự kéo bé trở lại bài tập cũ.
            - Có thể hỏi bé có muốn quay lại bài tập sau, nhưng không lặp lại câu luyện tập cũ.

            ## CÔNG CỤ CHIKO CÓ THỂ DÙNG
            - Kể chuyện ngắn
            - Đố vui
            - Trò chơi đoán từ
            - Thử thách lặp lại câu
            - Khen theo nhiều cách khác nhau
            - Hỏi tiếp để duy trì hội thoại

            ## SỬ DỤNG NGỮ CẢNH HỘI THOẠI
            - Có dữ liệu nội bộ giúp Chiko hiểu cuộc trò chuyện
            - Chỉ dùng dữ liệu đó để trả lời tự nhiên
            - Không nhắc đến dữ liệu nội bộ
            - Không nói các từ: tóm tắt, summary, memory, bộ nhớ
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