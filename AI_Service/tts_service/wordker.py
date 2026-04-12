from tts_service import run_inference

def main():
    while True:
        text = input("Nhap cau hoi ma ban muon chuyen thanh voice")
        run_inference(text ,"nuhanoi")
if __name__ == "__main__":
    main()
