import re

def clean_llm_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\n", ". ")  # xử lý trước
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*\*", "", text)
    text = re.sub(r"__(.*?)__", r"\1", text)
    text = re.sub(r"`+", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


if __name__ == "__main__":
    print(clean_llm_text("""
'Tuyệt vời!', 'Chiko rất vui khi bạn quyết định sẽ đi gặp bác sĩ để cảm thấy tốt hơn.', 'Bác sĩ sẽ là người bạn tuyệt vời giúp bạn khỏe lại đó!', 'Về việc học câu gì ư?', 'Chiko có một ý tưởng rất hay ho đây!', 'Khi bạn gặp bác sĩ, bạn có thể học cách nói bằng tiếng Anh một câu thật lễ phép và quan trọng để giới thiệu về mình đấy.', 'Bạn muốn học câu: **"Hello, doctor.', 'My name is [Tên của bạn]."** không?', 'Câu này có nghĩa là "Xin chào bác sĩ.', 'Tên cháu là [Tên của bạn]." Chiko nghĩ bác sĩ sẽ rất thích khi nghe bạn nói câu này đấy!', 'Bạn có muốn Chiko giúp bạn tập nói câu này không?', 'Hoặc bạn có muốn học một câu khác nữa không nào?"""))