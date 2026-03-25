import json
import torch
from http.server import BaseHTTPRequestHandler, HTTPServer

from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts

from tts_pipeline import (
    SAMPLE_RATE,
    clean_text,
    concat_wav_chunks,
    split_text_smartly,
    wav_to_pcm_stream,
)

MODEL_DIR = "model/"
latents_file = f"{MODEL_DIR}begai_lop_4_latents.pth"
device = "cuda:0" if torch.cuda.is_available() else "cpu"

config = XttsConfig()
config.load_json(f"{MODEL_DIR}config.json")
XTTS_MODEL = Xtts.init_from_config(config)
XTTS_MODEL.load_checkpoint(
    config,
    checkpoint_path=f"{MODEL_DIR}model.pth",
    vocab_path=f"{MODEL_DIR}vocab.json",
    use_deepspeed=False,
)
XTTS_MODEL.to(device)

latents = torch.load(latents_file, map_location=device, weights_only=True)
gpt_cond_latent = latents["gpt_cond_latent"].to(device)
speaker_embedding = latents["speaker_embedding"].to(device)

INFERENCE_KW = {
    "repetition_penalty": 5.0,
    "temperature": 0.7,
    "speed": 0.85,
}


class StreamingTTSHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length)
            request_json = json.loads(post_data.decode("utf-8"))
            input_text = request_json.get("text", "")

            self.send_response(200)
            self.send_header("Content-type", "audio/wav")
            self.send_header("Transfer-Encoding", "chunked")
            self.end_headers()

            parts = [clean_text(c) for c in split_text_smartly(input_text) if clean_text(c)]
            print(f"🚀 Bắt đầu Stream (sau ghép {len(parts)} chunk inference)...")

            wav_chunks = []
            with torch.inference_mode():
                for i, text_chunk in enumerate(parts):
                    outputs = XTTS_MODEL.inference(
                        text=text_chunk,
                        language="vi",
                        gpt_cond_latent=gpt_cond_latent,
                        speaker_embedding=speaker_embedding,
                        **INFERENCE_KW,
                    )
                    wav_chunks.append(outputs["wav"])
                    print(f"  ✅ Inference chunk {i + 1}/{len(parts)}")

            merged = concat_wav_chunks(wav_chunks, sample_rate=SAMPLE_RATE)
            for audio_data in wav_to_pcm_stream(merged, sample_rate=SAMPLE_RATE):
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
