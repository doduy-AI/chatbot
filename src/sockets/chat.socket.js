
const handleChatSocket = (wss) => {
    wss.on('connection', (ws, req) => {
        const user = req.user
        if (!user || !user.username) {
            console.log(" kết nối không hợp lệ ")
            ws.close()
            return
        }

        console.log(` Thiết lập đường truyền cho ${user.username}`)
        ws.on('message', (message) => {
            const msgString = message.toString();
            // console.log(` Nhận tin từ ${user.username}: ${msgString}`);
            const {text , language} = JSON.parse(message.toString())
            console.log(text)
            console.log(language)
            ws.send(`Bot nhận được: ${msgString} ${user.username}`);
        });

        ws.on('close', () => {
            console.log(` ${user.username} đã ngắt kết nối.`);
        });

        ws.on('error', (err) => {
            console.error(` Lỗi socket của ${user.username}:`, err.message);
        });

    })
}
module.exports = handleChatSocket;