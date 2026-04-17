import pyaudio
import threading
import time
import queue

class MicStreamer:
    def __init__(self):
        self.CHUNK = 1024
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
        self.audio_queue = queue.Queue()

        self.is_running = True      
        self.is_recording = False 

    def start(self):
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        print("[MIC] Mic ready...")

        while self.is_running:
            if self.is_recording:
                data = self.stream.read(self.CHUNK, exception_on_overflow=False)
                self.audio_queue.put(data)
            else:
                time.sleep(0.01)

    def start_recording(self):
        print("[MIC] Start Mic")
        self.is_recording = True

    def stop_recording(self):
        print("[MIC] Stop recording")
        self.is_recording = False

    def shutdown(self):
        self.is_running = False
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

if __name__ == "__main__":
    MIC = MicStreamer()
    MIC.start()
    
    time.sleep(1)
    MIC.start_recording()
    
    try:
        time.sleep(5) 
    except KeyboardInterrupt:
        pass
        
    MIC.stop_recording()
    MIC.shutdown()
