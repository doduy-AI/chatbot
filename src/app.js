require('dotenv').config();
const express = require('express');
const WebSocket = require('ws'); // Đảm bảo đúng hoa thường
const http = require('http');
const sequelize = require('./config/db');
const serverConfig = require('./config/server');
const { veryConnection } = require('./middlewares/auth.middleware');
const User = require('./model/user.model'); // Đảm bảo đúng đường dẫn file

const app = express();
const server = http.createServer(app);

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Router
const router = require("./router/index.router");
router(app);

// Error Handling
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ success: false, message: 'Internal Server Error' });
});

// 1. Khởi tạo WebSocket Server
const wss = new WebSocket.Server({
  server,
  verifyClient: veryConnection
});

// 2. Xử lý khi có kết nối thành công
wss.on('connection', (ws, req) => {
  // Lấy user từ req (đã được middleware gán vào)
  const user = req.user;

  // KIỂM TRA BẢO VỆ: Tránh crash nếu user undefined
  if (!user || !user.username) {
    console.log("⚠️ Kết nối không hợp lệ, đang đóng...");
    ws.close();
    return;
  }

  console.log(`📡 Thiết lập đường truyền cho: ${user.username}`);

  ws.on('message', (message) => {
    // message nhận được thường là Buffer, nên toString()
    const msgString = message.toString();
    console.log(`📩 Nhận tin từ ${user.username}: ${msgString}`);
    ws.send(`Bot nhận được: ${msgString}`);
  });

  ws.on('close', () => {
    console.log(`🔌 ${user.username} đã ngắt kết nối.`);
  });
});

// 3. Kết nối DB và chạy Server
sequelize
  .authenticate()
  .then(() => {
    console.log('✅ Kết nối database thành công!');
    return sequelize.sync({ alter: true });
  })
  .then(() => {
    console.log('✅ Đã sync models!');
    const PORT = serverConfig.PORT || 3000;
    server.listen(PORT, () => {
      console.log(`🚀 Server đang chạy tại http://localhost:${PORT}`);
    });
  })
  .catch((err) => {
    console.error('❌ Lỗi khởi động:', err.message);
    process.exit(1);
  });