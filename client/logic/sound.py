import pyaudio
import requests
import numpy as np
import time
class Speaker:
    def __init__(self, rate=48000 ,chunk=480):
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=rate,
            output=True,
            frames_per_buffer=chunk
        )
    def play(self, data):
        self.stream.write(data)

    def close(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

class Streaming_Aduio_Url:
    def __init__(self):
        self.TTS_CHANNELS = 1
        self.TTS_RATE = 24000
        self._pyaudio = pyaudio.PyAudio() 

    
    def play_audio_stream(self, url, is_playing_event, start_time=None):
        stream = None
        try:
            is_playing_event.set()
            stream = self._pyaudio.open(
                format=pyaudio.paInt16,
                channels=self.TTS_CHANNELS,
                rate=self.TTS_RATE,
                output=True,
                frames_per_buffer=4096
            )
            with requests.get(url, stream=True, timeout=10) as r:
                if r.status_code != 200:
                    return
                buffer = b""
                header_skipped = False
                first_chunk_time = None
                first_sound_time = None

                for chunk in r.iter_content(chunk_size=512):
                    if not chunk:
                        continue

                    if first_chunk_time is None:
                        first_chunk_time = time.time()
                        if start_time:
                            print(f"[LATENCY] end_mic → first chunk: {first_chunk_time - start_time:.3f}s")

                    buffer += chunk

                    if not header_skipped:
                        if len(buffer) < 44:
                            continue
                        buffer = buffer[44:]
                        header_skipped = True

                    usable = len(buffer) - (len(buffer) % 2)
                    if usable <= 0:
                        continue

                    data = buffer[:usable]
                    audio_np = np.frombuffer(data, dtype=np.int16)
                    energy = np.abs(audio_np).mean()

                    if first_sound_time is None and energy > 500:
                        first_sound_time = time.time()
                        if start_time and first_chunk_time:
                            print(f"[LATENCY] first chunk → first sound (silence padding): {first_sound_time - first_chunk_time:.3f}s")
                            print(f"[LATENCY] end_mic → first sound (tong): {first_sound_time - start_time:.3f}s")

                    stream.write(data)
                    buffer = buffer[usable:]

                if len(buffer) >= 2:
                    usable = len(buffer) - (len(buffer) % 2)
                    if usable > 0:
                        stream.write(buffer[:usable])

        except Exception as e:
            print(f"[TTS] Loi phat audio: {e}")
        finally:
            if stream is not None:
                try:
                    stream.stop_stream()
                    stream.close()
                except:
                    pass
            is_playing_event.clear()