from logic.data_mic import MicStreamer
from logic.sound import Speaker
from logic.ws_handler import WSClient
import time
WS = WSClient()
# MIC = MicStreamer()
# sound = Speaker()
# MIC.start()
# MIC.start_recording()




if __name__ == "__main__":
    WS.connect()
    try:
        while True:
            time.sleep(1) 
    except KeyboardInterrupt:
        print("Đang thoát...")

    
    # try:
    #     while True:
    #         frame = MIC.audio_queue.get()  
    #         sound.play(frame)
                    
    # except KeyboardInterrupt:
    #     print("\nĐang dừng...")
    # finally:
    #     MIC.stop_recording()
    #     MIC.shutdown()