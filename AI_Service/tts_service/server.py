import json
import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass

from http.server import BaseHTTPRequestHandler, HTTPServer

from tts_service import generate_tts


class StreamingTTSHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length)
            request_json = json.loads(post_data.decode("utf-8"))
            input_text = request_json.get("text", "")
            voice = request_json.get("voice", "nuhanoi")
            if voice not in ("nuhanoi", "nutreem"):
                voice = "nuhanoi"

            self.send_response(200)
            self.send_header("Content-type", "audio/wav")
            self.send_header("Transfer-Encoding", "chunked")
            self.end_headers()

            print(f"🚀 Stream TTS voice={voice} …")
            for audio_data in generate_tts(input_text, voice):
                chunk_size = hex(len(audio_data))[2:].encode("utf-8")
                self.wfile.write(chunk_size + b"\r\n")
                self.wfile.write(audio_data + b"\r\n")
                self.wfile.flush()

            self.wfile.write(b"0\r\n\r\n")

        except Exception as e:
            print(f"❌ Lỗi: {e}")


if __name__ == "__main__":
    port = 8000
    print(f"🚀 Server đang chạy tại http://localhost:{port}")
    HTTPServer(("", port), StreamingTTSHandler).serve_forever()
