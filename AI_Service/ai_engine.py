from google import genai
from config import settings

class AIEngine:
    def __init__(self):
        self.client = genai.Client(api_key=settings.API_LLM)

    def generate_respone(self , prompt: str):
            try:
                response = self.client.models.generate_content(
                model=settings.MODEL_NAME,
                contents=prompt
            )
                return response.text
            except Exception as e :
                print(f"[genAI ERROR] {e}")
                return "[genAI] {e}"
if __name__ == "__main__":
    ai = AIEngine()
    result = ai.generate_respone("hôm nay là ngày bao nhiêu")
    print(result)