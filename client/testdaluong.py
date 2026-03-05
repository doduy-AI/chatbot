# multi_client_tester.py
# Yêu cầu: pip install websocket-client requests
# Lưu ý: nếu muốn playback audio, thêm pyaudio, pydub, v.v. và set HEADLESS = False (not recommended for many parallel clients)

import threading
import time
import random
import json
import requests
import websocket
from typing import List, Dict
from collections import defaultdict

# --- CẤU HÌNH CHUNG ---
BASE_URL = "http://localhost:3000"
WS_URL = "ws://localhost:3000"
HEADLESS = True   # True = không phát audio (khuyến nghị cho load test), False = cố gắng phát
MESSAGES_PER_CLIENT = 10
MIN_DELAY_BETWEEN_MESSAGES = 0.5
MAX_DELAY_BETWEEN_MESSAGES = 2.0
# Nếu hệ thống yêu cầu rate-limit pause giữa kết nối: set thêm delay trước khi connect từng client
DELAY_BETWEEN_CLIENT_START = 0.2

# --- Helper: login để lấy token ---
def login_and_get_token(userdata: Dict[str, str]) -> str:
    try:
        res = requests.post(f"{BASE_URL}/auth/login", json=userdata, timeout=10)
        if res.status_code == 200:
            token = res.json().get("token")
            return token
        else:
            print(f"[{userdata['username']}] Login failed: {res.status_code} {res.text}")
            return None
    except Exception as e:
        print(f"[{userdata['username']}] Login error: {e}")
        return None

# --- TestClient class manages one simulated user ---
class TestClient:
    def __init__(self, username: str, password: str, questions: List[str], client_id: int):
        self.username = username
        self.password = password
        self.questions = questions
        self.client_id = client_id

        self.token = None
        self.ws = None

        # metrics
        self.sent_count = 0
        self.received_audio_count = 0
        self.latencies = []  # seconds
        self.errors = []

        # state to match requests -> replies
        self._pending_timestamps = {}  # message_id -> start_time

        # thread control
        self._stop_event = threading.Event()

    def _on_open(self, ws):
        print(f"[Client {self.client_id} {self.username}] WS opened.")
        # start sending messages in separate thread to avoid blocking ws callbacks
        threading.Thread(target=self._send_messages_loop, daemon=True).start()

    def _on_message(self, ws, message):
        try:
            data = json.loads(message)
        except Exception as e:
            print(f"[Client {self.client_id}] Failed parse message: {e}")
            return

        msg_type = data.get("type")
        if msg_type == "AI_VOICE_REPLY":
            # bot_text = data.get("text")
            audio_url = data.get("audioUrl")
            # compute latency: we measure time from last pending (we store a generic timestamp id)
            # If server echoes a timestamp or id, better match; here we just pop the oldest pending timestamp.
            if self._pending_timestamps:
                # pop arbitrary oldest
                oldest_key = sorted(self._pending_timestamps.keys())[0]
                start = self._pending_timestamps.pop(oldest_key)
                latency = time.time() - start
                self.latencies.append(latency)
                self.received_audio_count += 1
                print(f"[Client {self.client_id}] Received audioUrl after {latency:.3f}s")
            else:
                print(f"[Client {self.client_id}] Received AI_VOICE_REPLY but no pending timestamp tracked.")
            # Optionally, if not HEADLESS, download/playstream (not implemented here to keep stable)
            # you can call play_audio_stream(audio_url, ws) if you reuse your playback code.
        elif msg_type == "AI_VOICE_DONE":
            # server says done speaking
            pass
        elif msg_type == "STATUS":
            # ignore
            pass
        else:
            # other events
            print(f"[Client {self.client_id}] Other event: {data}")

    def _on_error(self, ws, err):
        print(f"[Client {self.client_id}] WS error: {err}")
        self.errors.append(str(err))

    def _on_close(self, ws, close_status_code, close_msg):
        print(f"[Client {self.client_id}] WS closed: {close_status_code} {close_msg}")

    def connect_and_run(self):
        # 1) login
        token = login_and_get_token({"username": self.username, "password": self.password})
        if not token:
            self.errors.append("login_failed")
            return

        self.token = token
        ws_url = f"{WS_URL}?token={self.token}"

        # create WebSocketApp
        self.ws = websocket.WebSocketApp(
            ws_url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close
        )

        # run_forever blocks; run in this thread
        try:
            # Note: run_forever will block until close; set dispatcher to run in thread
            self.ws.run_forever()
        except Exception as e:
            print(f"[Client {self.client_id}] run_forever error: {e}")
            self.errors.append(str(e))

    def _send_messages_loop(self):
        """
        Gửi MESSAGES_PER_CLIENT văn bản đến server, random chọn câu hỏi.
        Ghi lại timestamp trước khi ws.send để đo latency khi event AI_VOICE_REPLY về.
        """
        for i in range(MESSAGES_PER_CLIENT):
            if self._stop_event.is_set():
                break
            text = random.choice(self.questions)
            payload = {"text": text, "language": "VI", "timestamp": f"{int(time.time()*1000)}"}
            try:
                # store a pending timestamp keyed by message counter to match later.
                key = f"{int(time.time()*1000)}_{i}"
                self._pending_timestamps[key] = time.time()
                self.ws.send(json.dumps(payload))
                self.sent_count += 1
                # small random delay between messages to mimic users
                delay = random.uniform(MIN_DELAY_BETWEEN_MESSAGES, MAX_DELAY_BETWEEN_MESSAGES)
                time.sleep(delay)
            except Exception as e:
                print(f"[Client {self.client_id}] Error sending message: {e}")
                self.errors.append(str(e))
                break

        # after sending messages, wait a bit to receive responses, then close
        time.sleep(3)
        try:
            self.ws.close()
        except:
            pass

    def stop(self):
        self._stop_event.set()
        try:
            self.ws.close()
        except:
            pass

# --- Orchestrator: start N clients concurrently ---
def run_multi_clients(accounts: List[Dict[str, str]], questions: List[str]):
    clients = []
    threads = []

    for idx, acc in enumerate(accounts):
        client = TestClient(username=acc["username"], password=acc["password"], questions=questions, client_id=idx+1)
        t = threading.Thread(target=client.connect_and_run, daemon=True)
        clients.append(client)
        threads.append(t)
        t.start()
        time.sleep(DELAY_BETWEEN_CLIENT_START)  # slight stagger

    # Wait for threads to finish (they will close ws after sending)
    for t in threads:
        t.join(timeout=60)  # avoid forever blocking, tune as needed

    # Summary
    print("\n--- SUMMARY ---")
    total_sent = sum(c.sent_count for c in clients)
    total_received = sum(c.received_audio_count for c in clients)
    total_errors = sum(len(c.errors) for c in clients)
    print(f"Clients: {len(clients)} | Total sent: {total_sent} | Total audio replies received: {total_received} | Total errors: {total_errors}")
    for c in clients:
        avg_latency = (sum(c.latencies)/len(c.latencies)) if c.latencies else None
        print(f" - [{c.client_id}] {c.username}: sent={c.sent_count}, replies={c.received_audio_count}, avg_latency={avg_latency}, errors={len(c.errors)}")

    return clients

if __name__ == "__main__":
    # --- REPLACE: điền 5 account vào đây ---
    ACCOUNTS = [
        {"username": "duy1", "password": "123456"},
        {"username": "duy2", "password": "123456"},
        {"username": "duy3", "password": "123456"},
        {"username": "duy4", "password": "123456"},
        {"username": "duy5", "password": "123456"},
    ]

    # --- REPLACE: list ~10 câu hỏi / prompt ---
    QUESTIONS = [
        "Xin chào, bạn có thể giới thiệu về mình không?",
        "Hôm nay thời tiết ở Hà Nội thế nào?",
        "Cho tôi 3 mẹo tiết kiệm tiền hàng tháng.",
        "Làm sao để tạo một REST API bằng Node.js?",
        "Bạn đề xuất sách nào cho phát triển cá nhân?",
        "Giúp mình lên kế hoạch học tiếng Anh 3 tháng.",
        "Tại sao Docker lại hữu ích trong phát triển phần mềm?",
        "Cho ví dụ mã Python đọc file JSON.",
        "Cách debug memory leak trong ứng dụng Node?",
        "Gợi ý món ăn đơn giản với gạo và trứng."
    ]

    # chạy test
    run_multi_clients(ACCOUNTS, QUESTIONS)