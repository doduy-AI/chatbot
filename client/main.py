from logic.data_mic import MicStreamer
from logic.sound import Speaker
from logic.ws_handler import WSClient
import time
MIC = MicStreamer()
WS = WSClient(mic=MIC)
# sound = Speaker()
MIC.start()
MIC.start_recording()

info = {
        "voice":"nutrem",
    }

if __name__ == "__main__":
    WS.connect()
    print("[SYSTEM] Robot Chiko2 đang lắng nghe và gửi dữ liệu...")
    time.sleep(1)
    WS.send_json(info)
    try:
        while True:
            if MIC.is_recording:
                frame = MIC.audio_queue.get()  
                WS.send_bytes(frame)
            else:
                WS.send_bytes(MIC.get_silence_frame())  
                time.sleep(0.01)
    except KeyboardInterrupt:
        print("Đang thoát...")
