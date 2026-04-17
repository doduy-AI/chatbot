from login import Login
from input.data_mic import MicStreamer
from output.sound import Speaker
import time
import websocket
AUTH = Login()
MIC = MicStreamer()
sound = Speaker()
MIC.start()
MIC.start_recording()



# class WebSocketHandler:
#     def __init__(self):
#         print("[WS] WEBSOCKET")
#         self.ws = None
#         self.username = "bytehome"
#         self.password = "bytehome"
#         self.connectted = False
#         self.ws_url = AUTH.login_and_get_token(self.username,self.password)
    
#     def on_message(self, ws , message):

#     def connect(self):
#         self.ws = websocket.WebSocketApp(
#             self.ws_url,

#         )
#         return self.ws
    


if __name__ == "__main__":
    try:
        while True:
            if not MIC.audio_queue.empty():
                frame = MIC.audio_queue.get()
                sound.play(frame)
            else:
                    time.sleep(0.001)
                    
    except KeyboardInterrupt:
            print("\nĐang dừng...")
    finally:
            MIC.stop_recording()
            MIC.shutdown()