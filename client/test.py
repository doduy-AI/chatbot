import requests
import websocket
import threading
import json
import requests
import pyaudio

# --- CẤU HÌNH ---
BASE_URL = "http://localhost:3000"
WS_URL = "ws://localhost:3000"
USER_DATA = {
    "username": "duydd1",
    "password": "12345" 
}

CHANNELS = 1
RATE = 24000
CHUNK = 1024

p = pyaudio.PyAudio()
def play_audio_stream(url):
    """Hàm này sẽ 'húp' stream từ URL và đẩy ra loa ngay lập tức"""
    try:
        # Mở luồng HTTP GET tới Backend Fast API
        # stream=True để nhận dữ liệu theo từng mẩu (chunk)
        with requests.get(url, stream=True) as r:
            if r.status_code != 200:
                print(f" Lỗi: Không thể lấy audio từ {url}")
                return

            # Khởi tạo stream đầu ra cho loa
            stream = p.open(format=pyaudio.paInt16,
                            channels=CHANNELS,
                            rate=RATE,
                            output=True)

            print(" Đang phát âm thanh...")
            
            # Đọc từng mẩu dữ liệu từ HTTP và ghi thẳng vào loa
            for chunk in r.iter_content(chunk_size=CHUNK):
                if chunk:
                    stream.write(chunk)
            
            # Dọn dẹp sau khi phát xong
            stream.stop_stream()
            stream.close()
            print(" Đã phát xong.")
    except Exception as e:
        print(f" Lỗi phát âm thanh: {e}")

def login_and_get_token():
    try:
        print(f" Đang đăng nhập tài khoản: {USER_DATA['username']}...")
        response = requests.post(f"{BASE_URL}/auth/login", json=USER_DATA)
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('token')
            print(" Lấy Token thành công!")
            return token
        else:
            print(f" Đăng nhập thất bại: {response.text}")
            return None
    except Exception as e:
        print(f" Lỗi kết nối API: {e}")
        return None

def on_message(ws, message):
    data = json.loads(message)
    print(f"\n [BYTEHOME]: {data.get('text', '')}")
    
    # Nếu có audioUrl, tạo một luồng (thread) riêng để phát nhạc
    # Để tránh việc đang phát nhạc thì Robot bị "đơ" không nhận được tin nhắn tiếp theo
    audio_url = data.get("audioUrl")
    if audio_url:
        audio_thread = threading.Thread(target=play_audio_stream, args=(audio_url,))
        audio_thread.start()

    print(">> Bạn: ", end="", flush=True)
def on_open(ws):
    print(" WebSocket đã thông! Bạn có thể bắt đầu chat.")
    def send_loop():
        while True:
            msg = input(">> Bạn: ")
            if msg.lower() in ['exit', 'quit']:
                ws.close()
                break
            
            if msg.strip():
                
                data = {
                    "text": msg,
                    "language": "VI",
                    "timestamp": "" 
                }
                ws.send(json.dumps(data))
    threading.Thread(target=send_loop, daemon=True).start()


token = login_and_get_token()

if token:
    
    full_ws_url = f"{WS_URL}?token={token}"
    
    ws = websocket.WebSocketApp(
        full_ws_url,
        on_open=on_open,
        on_message=on_message,
        on_error=lambda ws, err: print(f"\n Lỗi WS: {err}"),
        on_close=lambda ws, c, m: print("\n  Đã đóng kết nối.")
    )
    ws.run_forever()