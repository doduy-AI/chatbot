import pyaudio

class Speaker:
    def __init__(self, rate=48000 ,chunk=320):
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