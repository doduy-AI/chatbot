import io
import json
import traceback
import wave
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass

from http.server import BaseHTTPRequestHandler, HTTPServer

from tts_pipeline import SAMPLE_RATE
from tts_service import AVAILABLE_VOICES, DEFAULT_VOICE, generate_tts


def _pcm_to_wav_bytes(pcm_s16le: bytes, sample_rate: int) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_s16le)
    return buf.getvalue()


class StreamingTTSHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print("%s - %s" % (self.address_string(), format % args))

    def do_GET(self):
        if self.path.rstrip("/") in ("", "/health"):
            body = json.dumps(
                {"ok": True, "voices": list(AVAILABLE_VOICES), "default": DEFAULT_VOICE},
                ensure_ascii=False,
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_error(404, "Not Found")

    def do_POST(self):
        try:
            raw_len = self.headers.get("Content-Length")
            if raw_len is None:
                self._send_json(411, {"error": "Content-Length required"})
                return
            content_length = int(raw_len)
            post_data = self.rfile.read(content_length)
            request_json = json.loads(post_data.decode("utf-8"))
            input_text = request_json.get("text", "")
            voice = request_json.get("voice", DEFAULT_VOICE)
            if voice not in AVAILABLE_VOICES:
                voice = DEFAULT_VOICE

            pcm = b"".join(generate_tts(input_text, voice))
            if not pcm:
                self._send_json(400, {"error": "empty text or no audio generated"})
                return

            wav_bytes = _pcm_to_wav_bytes(pcm, SAMPLE_RATE)
            self.send_response(200)
            self.send_header("Content-Type", "audio/wav")
            self.send_header("Content-Length", str(len(wav_bytes)))
            self.end_headers()
            self.wfile.write(wav_bytes)
        except json.JSONDecodeError as e:
            self._send_json(400, {"error": "invalid JSON", "detail": str(e)})
        except KeyError as e:
            self._send_json(400, {"error": str(e)})
        except Exception as e:
            traceback.print_exc()
            self._send_json(500, {"error": str(e)})

    def _send_json(self, code: int, obj: dict):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    port = 8000
    print(f"🚀 Server đang chạy tại http://localhost:{port}")
    HTTPServer(("", port), StreamingTTSHandler).serve_forever()
