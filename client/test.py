import websocket # pip install websocket-client

# Lấy token từ API Login của bạn
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjJlOGNmNTRmLThiNDQtNGFiNS04YmIxLTQ2ZmQ5NTkwNzAxMyIsInVzZXJuYW1lIjoiZHV5ZGQ2IiwiaWF0IjoxNzcxODY3MTQ3LCJleHAiOjE3NzQ0NTkxNDd9.LWjLNfjWGehmUWAJ9fNsfWHi3cnxD28HK8LKZZoFtGc"

# Thử kết nối
ws_url = f"ws://localhost:3000?token={TOKEN}"

def on_open(ws):
    print("✅ Kết nối thành công!")
    ws.send("Chào Server, tôi đã vào được sảnh VIP!")

def on_message(ws, message):
    print(f"🛰 Server phản hồi: {message}")

ws = websocket.WebSocketApp(ws_url, on_open=on_open, on_message=on_message)
ws.run_forever()