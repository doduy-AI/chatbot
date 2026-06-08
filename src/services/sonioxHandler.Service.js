const { SonioxNodeClient, RealtimeUtteranceBuffer } = require("@soniox/node");
const sonioxClient = new SonioxNodeClient();
async function handleRobotClient(ws, user, groupId, redisService) {
    let lastPushTime = 0;
    let currentVoiceStyle = 'nuhanoi';
    console.log(`[Robot] Khởi tạo Soniox session cho ${user.username}`);
    const session = sonioxClient.realtime.stt({
        model: 'stt-rt-v4',
        audio_format: 'pcm_s16le', 
        sample_rate: 48000, 
        num_channels: 1,
        language_hints: ['vi', 'en'],
        enable_endpoint_detection: true,
        endpoint_detection_config: {
            max_endpoint_delay_ms: 1500,
        },
    });

    const utteranceBuffer = new RealtimeUtteranceBuffer({ final_only: true });
    session.on('connected',()=>{
        console.log(`[Soniox] Session ready — ${user.username}`);
    })

    lastFinalText = ""
    let sentenceTimer = null;   
    session.on('result', (result) => {
        utteranceBuffer.addResult(result);

        const preview = result.tokens
            .filter(t => !t.is_final)
            .map(t => t.text)
            .join('');

        const finalText = result.tokens
            .filter(t => t.is_final)
            .map(t => t.text)
            .join('');

        if (preview) {
            ws.send(JSON.stringify({ type: 'STT_PREVIEW', text: preview }));
            console.log('PREVIEW:', preview);          
        if (sentenceTimer) {
                clearTimeout(sentenceTimer);
                sentenceTimer = setTimeout(() => {
                    if (lastFinalText) {
                        console.log('SENTENCE COMPLETE 1:', lastFinalText);
                        lastFinalText = "";
                    }
                    sentenceTimer = null;
                }, 1300);
            }
        }
        if (finalText) {
            console.log("final: " + finalText);
            lastFinalText += finalText;

            if (sentenceTimer) clearTimeout(sentenceTimer);
            sentenceTimer = setTimeout(async () => {
                
                console.log('SENTENCE COMPLETE 2:', lastFinalText);
                const now = Date.now();
                if (now - lastPushTime < 5000) {
                    lastFinalText = "";
                    sentenceTimer = null;
                    return;
                }
                lastPushTime = now;
                ws.send(JSON.stringify({ type: 'STATUS', content: 'end_mic_Bytehome' }));
                const task = {
                    userId: user.id,
                    groupId: groupId,
                    text: lastFinalText,
                    audio_format: "wav",
                    voice: currentVoiceStyle,
                    timestamp: Date.now()
                    };
                await redisService.pushTaskRobot(task);
                // await redisService.pushAgenTask(task)
                lastFinalText = "";
                sentenceTimer = null;
            }, 1300);
        }
    });

    
    session.on('error', (err) => {
        console.error(`[Soniox] Lỗi — ${user.username}:`, err);
        if (ws.readyState === ws.OPEN) {
            ws.send(JSON.stringify({ type: 'ERROR', content: 'Lỗi STT' }));
        }
    });

    session.on('finished', () => {
        console.log(`[Soniox] Session kết thúc — ${user.username}`);
    });

    try {
        await session.connect();
    } catch (err) {
        console.error(`[Soniox] Không kết nối được:`, err);
        ws.close();
        return;
    }

    ws.on('message', (data, isBinary) => {
        if (isBinary) {
            session.sendAudio(data);
        } else {
            try {
                const msg = JSON.parse(data.toString());
                currentVoiceStyle = msg.voice
                if (msg.type === 'stop') session.finish();
            } catch (_) {}
        }
    });

    ws.on('close', async () => {
        console.log(`[Robot] ${user.username} ngắt kết nối.`);
        await redisService.pushTask({
            userId: user.id,
            text: "disconectuser",
            timestamp: Date.now()
        });
        session.finish().catch(() => session.close());
    });

    ws.on('error', (err) => {
        console.error(`[Robot][WS] Lỗi:`, err);
        session.close();
    });

}

module.exports = { handleRobotClient };
