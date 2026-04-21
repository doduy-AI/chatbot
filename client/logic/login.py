
import requests
class Login:
    def __init__(self):
        self.LOCAL="118.70.187.211"
        self.PORT="4000"
        self.LOGIN_URL=f"http://{self.LOCAL}:{self.PORT}/auth/login"

    def login_and_get_token(self,username: str , password: str):
        try:
            print(f"[LOGIN] Login User {username} ...")
            data_payload = {
                "username" : username,
                "password" : password
            }
            res = requests.post(self.LOGIN_URL,json=data_payload)
            if res.status_code == 200 :
                WS_URL = f"ws://{self.LOCAL}:{self.PORT}?token={res.json().get('token')}"
                # print(WS_URL)
                return WS_URL
            else:
                print("[LOGIN] Đăng Nhập Thất bại")
                return "Login thất bại"
        except Exception as e :
            print(f"[LOGIN] Không thể kết lỗi đến server {e}")
        
if __name__ == "__main__":
    login = Login()
    print(login.login_and_get_token("bytehome","bytehome"))