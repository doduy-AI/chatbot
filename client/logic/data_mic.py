import pyaudio
import threading
import time
import queue

class MicStreamer:
    def __init__(self):
        self.CHUNK = 480
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 48000

        self.p = pyaudio.PyAudio()

        self.stream = self.p.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK
        )
        self.audio_queue = queue.Queue(maxsize=5)

        self.is_running = True      
        self.is_recording = False 

    def start(self):
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        while self.is_running:
            if self.is_recording:
                data = self.stream.read(self.CHUNK, exception_on_overflow=False)
                try:
                    self.audio_queue.put_nowait(data)
                except queue.Full:
                    self.audio_queue.get()  
                    self.audio_queue.put_nowait(data)  
            else:
                time.sleep(0.01)

    def start_recording(self):
        print("[MIC] Start Mic")
        self.is_recording = True
        if hasattr(self, 'ws_client') and self.ws_client:
            self.ws_client.send_json({"type": "start"})

    def stop_recording(self):
        print("[MIC] Stop recording")
        self.is_recording = False
        # Clear hết data cũ trong queue
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break

    def shutdown(self):
        self.is_running = False
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
        
    def get_silence_frame(self):
        return b'\x00' * self.CHUNK * 2 