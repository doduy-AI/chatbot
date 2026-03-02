import requests
import websocket
import threading
import json
import pyaudio
import speech_recognition as sr
import time
from pydub import AudioSegment
import io

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

# ======================================================
# 🔊 Phát âm thanh từ URL (chờ đến khi phát xong)
# ======================================================
def play_audio_stream(url: str):
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"⚠️ Không thể lấy audio từ {url}")
            return

        content_type = response.headers.get("Content-Type", "")
        format_guess = "mp3" if "mp3" in content_type or url.endswith(".mp3") else "wav"

        audio = AudioSegment.from_file(io.BytesIO(response.content), format=format_guess)
        raw_data = audio.raw_data

        stream = p.open(
            format=pyaudio.paInt16,
            channels=audio.channels,
            rate=audio.frame_rate,
            output=True
        )

        print("🔈 Đang phát phản hồi...")
        stream.write(raw_data)
        stream.stop_stream()
        stream.close()
        print("✅ Phát xong.\n")

    except Exception as e:
        print(f"💥 Lỗi phát âm thanh: {e}")

# ======================================================
# 🔐 Đăng nhập lấy token
# ======================================================
def login_and_get_token():
    try:
        print(f"🔑 Đăng nhập tài khoản: {USER_DATA['username']}...")
        res = requests.post(f"{BASE_URL}/auth/login", json=USER_DATA)
        if res.status_code == 200:
            token = res.json().get("token")
            print("✅ Lấy Token thành công!\n")
            return token
        else:
            print(f"❌ Đăng nhập thất bại: {res.text}")
            return None
    except Exception as e:
        print(f"💥 Lỗi kết nối API: {e}")
        return None

# ======================================================
# 🧠 STT - Nhận dạng giọng nói
# ======================================================
def recognize_once():
    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        print("🎙️ Đang lắng nghe bạn nói...")
        audio = recognizer.listen(source, phrase_time_limit=15)
        print("🧠 Đang xử lý giọng nói...")

    try:
        text = recognizer.recognize_google(audio, language="vi-VN").strip()
        if text:
            print(f"🗣️ Bạn nói: {text}")
        return text
    except sr.UnknownValueError:
        print("⚠️ Không nghe rõ, bỏ qua.")
        return ""
    except sr.RequestError as e:
        print(f"🚨 Lỗi STT: {e}")
        return ""

# ======================================================
# 💬 Nhận phản hồi từ server
# ======================================================
def on_message(ws, message):
    data = json.loads(message)
    msg_type = data.get("type")

    if msg_type == "AI_VOICE_REPLY":
        print(f"\n🤖 [BYTEHOME]: {data.get('text')}")
        print(f"🔊 Bot đang phát tại: {data.get('audioUrl')}")

    elif msg_type == "AI_VOICE_DONE":
        print("✅ Bot nói xong, quay lại lắng nghe bạn...")
        loop_speech_to_server(ws)

# ======================================================
# 🔁 Vòng lặp nghe → gửi → chờ phản hồi
# ======================================================
def loop_speech_to_server(ws):
    text = recognize_once()
    if text:
        data = {"text": text, "language": "VI", "timestamp": ""}
        ws.send(json.dumps(data))

# ======================================================
# 🌐 Kết nối WebSocket
# ======================================================
def on_open(ws):
    print("✅ WebSocket đã kết nối! Bắt đầu hội thoại bằng giọng nói...\n")
    loop_speech_to_server(ws)  # Bắt đầu vòng đầu tiên

# ======================================================
# 🚀 Main
# ======================================================
if __name__ == "__main__":
    token = login_and_get_token()
    if token:
        ws_url = f"{WS_URL}?token={token}"
        ws = websocket.WebSocketApp(
            ws_url,
            on_open=on_open,
            on_message=on_message,
            on_error=lambda ws, err: print(f"💥 Lỗi WS: {err}"),
            on_close=lambda ws, c, m: print("🔚 Kết nối WebSocket đã đóng.")
        )
        ws.run_forever()