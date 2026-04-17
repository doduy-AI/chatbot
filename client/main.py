from logic.data_mic import MicStreamer
from logic.sound import Speaker
from logic.ws_handler import WSClient
import time
WS = WSClient()
MIC = MicStreamer()
# sound = Speaker()
MIC.start()
MIC.start_recording()

if __name__ == "__main__":
    WS.connect()
    print("[SYSTEM] Robot Chiko2 đang lắng nghe và gửi dữ liệu...")
    try:
        while True:
            frame = MIC.audio_queue.get()  
            if frame:
                WS.send_bytes(frame)
    except KeyboardInterrupt:
        print("Đang thoát...")
