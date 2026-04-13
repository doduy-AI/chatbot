from tts_service import run_inference

if __name__ == "__main__":
    while True:
        text = input("Mời bạn nhập text : ")
        voice = "nuhanoi"
        run_inference(text,voice)
