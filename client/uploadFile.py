import os
import requests

# --- CẤU HÌNH ---
API_URL = 'http://localhost:3000/api/admin/rag/uploadfile'
TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ImJlNDBmZTk0LTIyMGMtNDA4NS05YThkLWM0ODAwMTlhYzk2MCIsInVzZXJuYW1lIjoiYnl0ZWhvbWUiLCJpYXQiOjE3NzMxOTUyNzgsImV4cCI6MTc3NTc4NzI3OH0.QBFVKMudtjAu41Hl2RKoWNH1oPQJJ6PEGE1Ues8lNcs'  # Dán token của bạn vào đây
TARGET_DIR = '/home/doduy/Downloads/data_cminh'  # Thư mục chứa 1000 file (có folder con)
GROUP_ID = '4cf8e736-fe58-4d5a-bd91-16f5fe67f68e' # Thêm GroupID của bạn vào đây

def get_all_files_recursive(directory):
    """Quét sạch mọi file trong mọi ngóc ngách thư mục con"""
    file_list = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            full_path = os.path.abspath(os.path.join(root, file))
            file_list.append(full_path)
    return file_list

def start_upload_all():
    # 1. Quét toàn bộ file
    print(f"🔍 Đang quét sạch thư mục: {TARGET_DIR}...")
    all_files = get_all_files_recursive(TARGET_DIR)
    total = len(all_files)
    
    if total == 0:
        print("❌ Không thấy file nào để upload!")
        return

    print(f"🚀 Tìm thấy {total} file. Đang chuẩn bị gửi...")

    headers = {'Authorization': f'Bearer {TOKEN}'}
    
    # 2. Chuẩn bị dữ liệu (Form-data)
    # Lưu ý: key phải là 'groupId' giống hệt trong ảnh bạn gửi
    data_payload = {
        'groupId': GROUP_ID 
    }

    files_payload = []
    opened_files = []

    try:
        for file_path in all_files:
            f = open(file_path, 'rb')
            opened_files.append(f)
            # 'files' khớp với key trong ảnh
            files_payload.append(('files', (os.path.basename(file_path), f)))

        print(f"📤 Đang 'vụt' {total} file lên server...")
        
        # Khi truyền cả data và files, requests sẽ tạo format multipart/form-data
        # y hệt như cách Postman thực hiện trong ảnh của bạn.
        response = requests.post(
            API_URL, 
            headers=headers, 
            data=data_payload, 
            files=files_payload,
            timeout=1200
        )

        if response.status_code == 200:
            print(f"✅ Thành công rực rỡ!")
            print("Response:", response.json())
        else:
            print(f"❌ Server từ chối (Status {response.status_code}): {response.text}")

    except Exception as e:
        print(f"⚠️ Lỗi hệ thống: {e}")
    
    finally:
        for f in opened_files:
            f.close()

if __name__ == "__main__":
    start_upload_all()