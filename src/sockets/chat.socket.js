const redisService = require('../services/redisService');

const handleChatSocket = (wss) => {
    
    // Khởi động trình nghe phản hồi từ AI ngay khi server chạy
    redisService.listenForResponses((data) => {
        // data = { userId: "ddduy2", reply: "...", status: "success" }
        
        // Tìm đúng client đang kết nối để gửi trả kết quả
        wss.clients.forEach((client) => {
            if (client.readyState === 1 && client.user?.username === data.userId) {
                client.send(JSON.stringify({
                    type: 'AI_REPLY',
                    content: data.reply,
                    audioUrl: data.audioUrl || null 
                }));
            }
        });
    });

    wss.on('connection', (ws, req) => {
        const user = req.user;
        if (!user || !user.username) {
            ws.close();
            return;
        }

        ws.on('message', async (message) => {
            try {
                const msgString = message.toString();
                const payload = JSON.parse(msgString);

                // Tạo task để gửi sang Python
                const task = {
                    userId: user.username,
                    text: payload.text,
                    language: payload.language || 'vi',
                    timestamp: Date.now()
                };

                await redisService.pushTask(task);

                ws.send(JSON.stringify({ type: 'STATUS', content: 'Đang xử lý...' }));

            } catch (err) {
                console.error("Lỗi format tin nhắn:", err.message);
                ws.send(JSON.stringify({ type: 'ERROR', content: 'Định dạng gửi không đúng (JSON)' }));
            }
        });

        ws.on('close', () => console.log(`${user.username} ngắt kết nối.`));
    });
};

module.exports = handleChatSocket;