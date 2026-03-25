"""
Xuất WAV từng dòng trong docs/cau-test.txt — kiểm thử vỡ giọng / hụt hơi.

  cd AI_Service/tts_service
  python export_cau_test_wav.py --out ../../tts_test_output/sau_fix

  python export_cau_test_wav.py --dry-run   # không cần model: chỉ in cách tách chunk

Tuỳ chọn: --voice nuhanoi|nutreem  --input path/to/cau-test.txt
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# HERE = .../chatbot_voice/AI_Service/tts_service  ->  parents[1] = chatbot_voice
REPO_ROOT = HERE.parents[1]
MODEL_DIR = HERE / "model"

os.chdir(HERE)
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def _required_model_files(voice: str) -> list[Path]:
    refs = {
        "nuhanoi": MODEL_DIR / "giongnuhanoi6s.wav",
        "nutreem": MODEL_DIR / "nutrem.wav",
    }
    return [
        MODEL_DIR / "model.pth",
        MODEL_DIR / "config.json",
        MODEL_DIR / "vocab.json",
        refs[voice],
    ]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--voice", default="nuhanoi", choices=["nuhanoi", "nutreem"])
    p.add_argument(
        "--input",
        type=Path,
        default=REPO_ROOT / "docs" / "cau-test.txt",
        help="File UTF-8, mỗi dòng một đoạn test",
    )
    p.add_argument(
        "--out",
        type=Path,
        default=REPO_ROOT / "tts_test_output" / "sau_fix",
        help="Thư mục ghi file 001.wav ...",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Chỉ kiểm tra tách câu (không load XTTS, không cần model.pth)",
    )
    args = p.parse_args()

    if not args.input.is_file():
        print("Không thấy file input:", args.input)
        sys.exit(1)

    lines = [
        ln.strip()
        for ln in args.input.read_text(encoding="utf-8").splitlines()
        if ln.strip()
    ]
    if not lines:
        print("File input rỗng.")
        sys.exit(1)

    if args.dry_run:
        from tts_pipeline import clean_text, split_text_smartly  # noqa: E402

        report = REPO_ROOT / "tts_test_output" / "dry_run_chunk_report.txt"
        report.parent.mkdir(parents=True, exist_ok=True)
        buf: list[str] = []
        print(f"Dry-run: {len(lines)} dòng → báo cáo chunk (không cần GPU/model)\n")
        for i, text in enumerate(lines, start=1):
            chunks = [clean_text(c) for c in split_text_smartly(text) if clean_text(c)]
            buf.append(f"=== Dòng {i:03d} ({len(chunks)} chunk) ===\n")
            for j, c in enumerate(chunks, start=1):
                preview = c if len(c) <= 200 else c[:197] + "..."
                buf.append(f"  [{j}] ({len(c)} ký tự) {preview}\n")
            buf.append("\n")
            print(f"  {i:03d}: {len(chunks)} chunk")
        report.write_text("".join(buf), encoding="utf-8")
        print(f"\nĐã ghi chi tiết: {report}")
        return

    missing = [str(f) for f in _required_model_files(args.voice) if not f.is_file()]
    if missing:
        print("Thiếu file để chạy TTS thật (chưa xuất được WAV):")
        for m in missing:
            print("  -", m)
        print(
            "\nHãy copy model.pth + file giọng ref vào AI_Service/tts_service/model/ "
            "(hoặc tải checkpoint XTTS v2 đúng repo Coqui), rồi chạy lại lệnh không --dry-run."
        )
        print("Vẫn có thể chạy: python export_cau_test_wav.py --dry-run")
        sys.exit(2)

    import numpy as np  # noqa: E402
    import soundfile as sf  # noqa: E402

    from tts_pipeline import SAMPLE_RATE  # noqa: E402
    from tts_service import generate_tts  # noqa: E402

    args.out.mkdir(parents=True, exist_ok=True)
    print(f"Xuất {len(lines)} file → {args.out} (voice={args.voice})")
    for i, text in enumerate(lines, start=1):
        name = f"{i:03d}.wav"
        out_path = args.out / name
        pcm = b"".join(generate_tts(text, args.voice))
        arr = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32767.0
        sf.write(str(out_path), arr, SAMPLE_RATE, subtype="PCM_16")
        print(f"  OK {name} ({len(arr) / SAMPLE_RATE:.1f}s)")

    print("Xong. Nghe thử toàn bộ thư mục và đối chiếu với baseline (nếu có).")


if __name__ == "__main__":
    main()
