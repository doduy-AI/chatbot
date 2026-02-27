⚙️ Chatbot Backend Microservice (RAG System)Dự án này là một hệ thống Chatbot thông minh xây dựng theo kiến trúc Microservices, tích hợp kỹ thuật RAG (Retrieval-Augmented Generation) để trả lời câu hỏi dựa trên tài liệu cá nhân của người dùng. Hệ thống hỗ trợ giao tiếp thời gian thực qua WebSocket và xử lý tác vụ nền bằng Redis Queue.🧠 Kiến Trúc Hệ ThốngHệ thống bao gồm 3 thành phần chính hoạt động độc lập:Backend (Node.js/Express):Quản lý người dùng (Đăng ký/Đăng nhập với JWT).Tiếp nhận file tài liệu (.txt, .docx) qua REST API.Xử lý giao tiếp thời gian thực qua WebSocket.Đẩy tác vụ vào Redis Queue cho các service AI.AI Chat Service (Python):Lắng nghe tác vụ chat từ Redis.Tìm kiếm ngữ nghĩa (Semantic Search) trên Vector DB (Qdrant).Sử dụng Google Gemini AI để tạo câu trả lời dựa trên ngữ cảnh tìm được.Embedding Service (Python):Xử lý tài liệu người dùng upload.Chuyển đổi văn bản thành Vector (Embedding) sử dụng model sentence-transformers.Lưu trữ và lập chỉ mục vào Qdrant Vector DB.🛠 Công Nghệ Sử DụngLớpCông nghệLập trìnhNode.js, Python 3.10Cơ sở dữ liệuPostgreSQL (User data), Qdrant (Vector DB)Truyền tinRedis (Message Queue & Pub/Sub)AI/ML ModelsGoogle Gemini (LLM), Sentence Transformers (Embedding)Ảo hóaDocker, Docker Compose🚀 Hướng Dẫn Cài Đặt1. Cấu hình môi trườngTạo file .env tại thư mục gốc và các thư mục service tương ứng với các biến sau:PORT: Cổng chạy Backend (mặc định 3000).API_LLM: API Key của Google Gemini.HOST_DB, USER_DB, PASS_DB: Thông tin kết nối PostgreSQL.HOST_REDIS, PORT_REDIS: Thông tin kết nối Redis.QDRANT_HOST, QDRANT_PORT: Thông tin kết nối Qdrant.2. Khởi chạy cơ sở hạ tầng (Docker)Bashdocker-compose up -d db redis qdrant
3. Chạy Backend (Node.js)Bashnpm install
npm start
4. Chạy các AI Service (Python)Cài đặt thư viện:Bashpip install -r AI_Service/chat_service/requirements.txt
pip install -r AI_Service/embetdding_service/requirements.txt
Chạy Worker:Chat Worker: python AI_Service/chat_service/worker.pyEmbedding Worker: python AI_Service/embetdding_service/worker_embetdding.py📁 Cấu Trúc Thư Mục ChínhPlaintext├── AI_Service/
│   ├── chat_service/       # Xử lý phản hồi từ LLM & RAG
│   ├── embetdding_service/ # Xử lý tài liệu thành Vector
│   └── config/             # Cấu hình chung cho Python services
├── src/
│   ├── controllers/        # Xử lý logic API (Auth, RAG)
│   ├── middlewares/        # Xác thực JWT & Upload
│   ├── services/           # Giao tiếp Redis
│   └── sockets/            # Quản lý WebSocket
├── uploads/                # Lưu trữ tài liệu tạm thời theo userId
└── docker-compose.yml      # Cấu hình triển khai container
📝 Quy Trình Hoạt ĐộngHuấn luyện (Embedding): Người dùng upload file -> Backend lưu vào thư mục riêng -> Đẩy task vào Redis -> Embedding Service đọc file, cắt đoạn (chunking), tạo vector và lưu vào Qdrant.Hỏi đáp (Chat): Người dùng gửi tin nhắn qua WebSocket -> Backend đẩy task vào Redis -> Chat Service lấy vector câu hỏi -> Tìm đoạn văn liên quan trong Qdrant -> Gửi kèm prompt vào Gemini -> Trả kết quả về WebSocket cho người dùng.👨‍💻 Tác giảĐỗ Đình Duy (doduy-AI)Email: dodinhduy203@gmail.comDự án: Chatbot Backend Microservice trợ lý ảo thông minh.Lưu ý: Đảm bảo đã khởi tạo các thư mục uploads và cài đặt đầy đủ các phụ thuộc trước khi khởi chạy.
