import os
_DIR = os.path.dirname(os.path.abspath(__file__))

VOICE_PROFILE = {
    "nutrem":{
        "ref_audio":os.path.join(_DIR ,"./nutrem.wav"),
        "ref_text":"Xin chào, hôm nay là một ngày khá đặc biệt. Không phải vì có điều gì đó quá lớn lao xảy ra, mà đơn giản là tôi quyết định sẽ làm mọi thứ chậm lại một chút, để lắng nghe bản thân mình rõ hơn."
    },

    "nuhanoi":{
        "ref_audio":os.path.join(_DIR ,"./giongnuhanoi6s.wav"),
        "ref_text":"Xin chào, tôi là một người yêu thích công nghệ và sáng tạo. Trong công việc hằng ngày, tôi thường đọc tài liệu"
    }
}