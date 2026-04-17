import websocket
import threading
import json
from .login import Login 



LOGIN = Login()

class WSClient:
    def __init__(self):
        self.username = "chiko"
        self.password = "123456"
        self.url = LOGIN.login_and_get_token(self.username,self.password)
        self.ws =None
        self.is_connected = False

    def on_message(self,ws,message):
        print(f"[WS] Nhận Phản hồi từ Server {message}")

    def on_error(self,ws,error):
        print(f"[WS] Lỗi : {error}")
    
    def on_close(self, ws, close_status_code, close_msg):
        print(" [WS] Đã ngắt kết nối ")
        self.is_connected = False

    def on_open(self, ws):
        print("[WS] Kết nối thành công!")
        self.is_connected = True
    def connect(self):
        # Tạo kết nối chạy ngầm để không chặn code chính
        self.ws = websocket.WebSocketApp(
            self.url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        threading.Thread(target=self.ws.run_forever, daemon=True).start()

    def send_bytes(self, data):
        if self.is_connected:
            self.ws.send(data, opcode=websocket.ABNF.OPCODE_BINARY)

    def send_json(self, data):
        try:
            json_data = json.dumps(data)
            self.ws.send(json_data)
            
        except Exception as e:
            print(f"[ERROR] Không thể gửi JSON: {e}")