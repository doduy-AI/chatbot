const redisService = require('../services/redisService');
const User = require('../model/user.model')
const Prompt = require('../model/group_prompt.model')
const SummaryPrompts = require('../model/summary_prompt.model')
const { handleRobotClient } = require('../services/sonioxHandler.Service');
const handleChatSocket = (wss) => {
    redisService.listenForResponses((userId, data) => {
        wss.clients.forEach((client) => {
            if (client.readyState === 1 && client.user && String(client.user.id) === String(userId)) {
                client.send(JSON.stringify({
                    type: 'AI_VOICE_REPLY',
                    text: data.text,
                    audioUrl: data.audioUrl,
                }));
            }
        });
    });
// client kết nối ws đến server 
    wss.on('connection', async (ws, req) => {
        const user = req.user;
        const userGroup = await User.findOne({
        where:{
            id:user.id,
        }
        })
        const groupId = userGroup.groupId

        if (!user || !user.id) {
            console.log("Kết nối bị từ chối: Không có thông tin User");
            ws.close();
            return;
        }
        ws.user = user;
        const cacheKey = `group:${groupId}:content`;
        const cacheKeySummary = `summary:${groupId}:summary`;

        let content = await redisService.getCache(cacheKey)
        let summary = await redisService.getCache(cacheKeySummary);

        if (!content || !summary ) {
            console.log(`[Cache MISS] group ${groupId} → Đang lấy dữ liệu từ DB...`);

            const promptGroup = await Prompt.findOne({
                where:{
                    groupId:groupId
                }
            })
            if (promptGroup) {
                content = promptGroup.content 
                await redisService.setCache(cacheKey, content, 3600);
                const summaryData = await SummaryPrompts.findOne({ where: { promptId: promptGroup.id } });
                if (summaryData) {
                    summary = summaryData.summary_prompt;
                    await redisService.setCache(cacheKeySummary, summary, 3600);
                    console.log(`[Cache MISS] group ${groupId} → đã lưu cache ${cacheKeySummary}`);
                }
            }
            console.log(`[Cache MISS] group ${groupId} → đã lưu cache`);

            }
            

        console.log(`[Socket] ${user.username} đã kết nối .`);
        if (userGroup.clientType === 'robot') {
            handleRobotClient(ws, user, groupId, redisService);
        } else {
            handleHumanClient(ws, user, groupId);
        }

    function handleHumanClient(ws, user, groupId) {
        ws.on('message', async (message) => {
            try {
                const msgString = message.toString();
                const payload = JSON.parse(msgString);

                const task = {
                    userId: user.id,
                    groupId:groupId,
                    text: payload.text,
                    voice:payload.voice,
                    audio_format:"mp3",
                    language: payload.language || 'vi',
                    timestamp: Date.now()
                };

                await redisService.pushTask(task);

                ws.send(JSON.stringify({
                    type: 'STATUS',
                    content: 'Hệ thống đang sinh giọng nói...'
                }));

            } catch (err) {
                console.error("Lỗi xử lý tin nhắn:", err.message);
                ws.send(JSON.stringify({ type: 'ERROR', content: 'Lỗi xử lý yêu cầu' }));
            }
        });
        }

        ws.on('close', async () => {console.log(`${user.username} ngắt kết nối.`);
            const task = {
                    userId: user.id,
                    text:"disconectuser",
                    timestamp: Date.now()
                };
        await redisService.pushTask(task)
        });
        
    });
};

module.exports = handleChatSocket;