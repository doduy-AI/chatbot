import requests
import websocket
import threading
import json
import pyaudio
import speech_recognition as sr
import time
from pydub import AudioSegment
import io
import sys



# --- CẤU HÌNH ---
BASE_URL = "http://localhost:3000"
WS_URL = "ws://localhost:3000"
USER_DATA = {
    "username": "bytehome",
    "password": "123456"
}

CHANNELS = 1
RATE = 24000
CHUNK = 1024

p = pyaudio.PyAudio()
recognizer = sr.Recognizer()
mic = sr.Microphone()

# Biến trạng thái (tránh global)
STATE = {
    "start_request_time": 0
}

# Màu log
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"



QUESTION_LIST = [
   
    "Mở cho mình bản nhạc không lời để tập trung học bài.",
    "Bạn có thấy mình là một học sinh chăm chỉ không?",
    "Can you teach me a new English word today?",
    "Hãy giúp mình lập kế hoạch làm bài tập hôm nay.",
    "Đố bạn, tại sao chúng ta cần uống nhiều nước?",
    "How can I be a hero to the planet?",
    "Hãy kể cho mình nghe một sự thật thú vị về loài cá mập.",
    "Bạn có thích đi học không?",
    "Can we practice my English speaking skills?",
    "Làm thế nào để viết một bức thư cho bạn thân?",
    "Đố bạn, con gì ngủ trong khi đứng?",
    "Help me choose a cool name for my robot toy.",
    "Tại sao lá cây lại có màu xanh?",
    "Can you tell me how to draw a simple spaceship?",
    "Mình đã làm xong bài tập, hãy cho mình một lời khen nhé!",
    "ByteHome, tắt đèn để mình đi ngủ sớm lấy sức học bài nhé."
]
CURRENT_INDEX = 0

def auto_loop_speech_to_server(ws):
    """
    Tự động gửi câu hỏi từ danh sách thay vì dùng micro.
    """
    global CURRENT_INDEX
    
    if CURRENT_INDEX < len(QUESTION_LIST):
        text = QUESTION_LIST[CURRENT_INDEX]
        print(f"{CYAN}🤖 [AUTO] Gửi câu hỏi: {text}{RESET}")
        
        # ⏱ Bắt đầu đo từ lúc gửi text đi
        STATE["start_request_time"] = time.time()
        data = {"text": text, "language": "VI", "timestamp": ""}
        ws.send(json.dumps(data))
        
        CURRENT_INDEX += 1
    else:
        print(f"{GREEN}🎉 Đã chạy hết danh sách câu hỏi!{RESET}")


def play_audio_stream(url: str, ws):
    try:
        stream = p.open(
            format=pyaudio.paInt16,
            channels=CHANNELS,
            rate=RATE,
            output=True
        )

        with requests.get(url, stream=True) as r:
            if r.status_code != 200:
                stream.close()
                return

            first_chunk = True

            for chunk in r.iter_content(chunk_size=4096):
                if not chunk:
                    continue

                # Skip 44 bytes WAV header ở chunk đầu tiên
                if first_chunk:
                    chunk = chunk[44:]
                    first_chunk = False
                    if not chunk:  # Nếu chunk chỉ có header thì bỏ qua
                        continue

                stream.write(chunk)

        stream.stop_stream()
        stream.close()
        auto_loop_speech_to_server(ws)

    except Exception as e:
        print(f"{YELLOW}⚠️  Lỗi: {e}{RESET}")
        if 'stream' in locals():
            stream.stop_stream()
            stream.close()

def login_and_get_token():
    """
    Đăng nhập để lấy token từ API backend.
    """
    try:
        print(f"🔐 Đăng nhập tài khoản: {USER_DATA['username']}...")
        res = requests.post(f"{BASE_URL}/auth/login", json=USER_DATA)
        if res.status_code == 200:
            token = res.json().get("token")
            print(f"{GREEN}✅ Lấy Token thành công!{RESET}\n")
            return token
        else:
            print(f"{YELLOW}❌ Đăng nhập thất bại: {res.text}{RESET}")
            return None
    except Exception as e:
        print(f"{YELLOW}⚠️  Lỗi kết nối API: {e}{RESET}")
        return None


def recognize_once():
    """
    Ghi âm và nhận diện giọng nói 1 lần.
    """
    with mic as source:
        print("🎤 Chuẩn bị ghi âm...")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        print("🎧 Đang lắng nghe bạn nói...")
        audio = recognizer.listen(source, phrase_time_limit=15)
        print("🧠 Đang xử lý giọng nói...")

    try:
        text = recognizer.recognize_google(audio, language="vi-VN").strip()
        if text:
            print(f"{CYAN}💬 Bạn nói: {text}{RESET}")
        return text
    except sr.UnknownValueError:
        print(f"{YELLOW}⚠️  Không nghe rõ, bỏ qua.{RESET}")
        return ""
    except sr.RequestError as e:
        print(f"{YELLOW}⚠️  Lỗi STT: {e}{RESET}")
        return ""


def loop_speech_to_server(ws):
    """
    Gửi text (STT) từ mic lên server qua WebSocket.
    """
    text = recognize_once()
    if text:
        # ⏱ Bắt đầu đo từ lúc gửi text đi
        STATE["start_request_time"] = time.time()
        data = {"text": text, "language": "VI", "timestamp": ""}
        ws.send(json.dumps(data))
    else:
        loop_speech_to_server(ws)


def on_message(ws, message):
    """
    Xử lý tin nhắn WebSocket nhận được từ server.
    """
    data = json.loads(message)
    msg_type = data.get("type")

    if msg_type == "AI_VOICE_REPLY":
        bot_text = data.get("text")
        audio_url = data.get("audioUrl")
        print(bot_text)
        print(audio_url)

        # ⏱ Tính thời gian từ lúc gửi text đến khi có audioUrl
        if STATE["start_request_time"] > 0:
            latency = time.time() - STATE["start_request_time"]
            print(f"{YELLOW}⏱ Latency (Text -> audioUrl): {latency:.2f} giây{RESET}")
            STATE["start_request_time"] = 0

        if bot_text:
            print(f"\n{GREEN}[BYTEHOME]: {bot_text}{RESET}")

        if audio_url:
            play_audio_stream(audio_url, ws)

    elif msg_type == "AI_VOICE_DONE":
        print(f"{CYAN}🤖 Bot nói xong, quay lại lắng nghe bạn...{RESET}")
        auto_loop_speech_to_server(ws)

    else:
        # Bỏ qua STATUS event (không đo latency)
        if msg_type != "STATUS":
            print(f"{YELLOW}⚠️  Event không xác định: {data}{RESET}")


def on_open(ws):
    
    print(f"{GREEN}✅ WebSocket đã kết nối! Bắt đầu hội thoại bằng giọng nói...{RESET}\n")
    auto_loop_speech_to_server(ws)


if __name__ == "__main__":
    token = login_and_get_token()
    if token:
        ws_url = f"{WS_URL}?token={token}"
        ws = websocket.WebSocketApp(
            ws_url,
            on_open=on_open,
            on_message=on_message,
            on_error=lambda ws, err: print(f"{YELLOW}⚠️  Lỗi WS: {err}{RESET}"),
            on_close=lambda ws, c, m: print(f"{YELLOW}🔌 Kết nối WebSocket đã đóng.{RESET}")
        )
        ws.run_forever()