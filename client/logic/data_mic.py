import pyaudio
import threading
import time
import queue
import numpy as np 
from pedalboard import NoiseGate  , Pedalboard

class MicStreamer:
    def __init__(self):
        self.CHUNK = 480
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 48000
        self.RMS_THRESHOLD = 300

        self.board= Pedalboard([
            NoiseGate(
                threshold_db=-60,
                ratio=3,
                attack_ms=2.0,
                release_ms=150.0
            )
        ])

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

    def _process(self, chunk):
        audio_np = np.frombuffer(chunk, dtype=np.int16).astype(np.float32) / 32768.0
        
        rms = np.abs(audio_np).mean()
        # print(f"RMS: {rms:.4f}")
        
        if rms < 0.005:
            return self.get_silence_frame()
        
        return chunk

    def _loop(self):
        while self.is_running:
            if self.is_recording:
                data = self.stream.read(self.CHUNK, exception_on_overflow=False)
                processed = self._process(data)  
                try:
                    self.audio_queue.put_nowait(processed)  
                except queue.Full:
                    self.audio_queue.get()
                    self.audio_queue.put_nowait(processed)
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
