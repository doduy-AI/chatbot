const Redis = require('ioredis')
const config = require("../config/server")


const redisPublisher = new Redis({
    host: config.HOST_REDIS,
    port: config.PORT_REDIS
})

const redisSubscriber = new Redis({
    host: config.HOST_REDIS,
    port: config.PORT_REDIS
})

class RedisService {
    constructor() {
        this.queueName = 'ai_tasks';
        this.embeddingQueue = 'embedding_tasks';
        this.embeddingResponseChannel = 'embedding_responses';
        this.voiceResponsePattern = 'voice_ready:*';
        this.chatQueue = "chat"
        this.chatRespon = "chat-respone"
        this.initPatternListener();
    }
    initPatternListener() {
        redisSubscriber.on('pmessage', (pattern, channel, message) => {
            try {
                const data = JSON.parse(message);
                if (pattern === this.voiceResponsePattern) {
                    const userId = channel.split(':')[1];
                    if (this.voiceCallback) this.voiceCallback(userId, data);
                }

            } catch (err) {
                console.error('[Redis] Lỗi parse JSON:', err);
            }
        });
    }

// lắng nghe phản hồi voice 
    listenForResponses(callback) {
        this.voiceCallback = callback;
        redisSubscriber.psubscribe(this.voiceResponsePattern);
        console.log(`[Redis] Đang nghe Pattern: ${this.voiceResponsePattern}`);
    }
// lắng nghe phản hồi voice
    listenForResponsesChat(callback) {
        this.voiceCallback = callback;
        redisSubscriber.psubscribe(this.chatRespon);
        console.log(`[Redis] Đang nghe Pattern: ${this.chatRespon}`);
    }
    

    // ai task
    async pushTask(task) {
        try {
            const data = JSON.stringify(task)
            await redisPublisher.lpush(this.queueName, data);
        } catch (err) {
            console.error('[Redis] lỗi push task ', err)
            throw err
        }
    }
    // embetding task 
    async pushEmbeddingTask(task) {
        try {
            const data = JSON.stringify(task);
            await redisPublisher.lpush(this.embeddingQueue, data);
        } catch (err) {
            console.error('[Redis] lỗi push embedding task', err);
            throw err;
        }
    }

    // chat task 
    async pushChatTask(task){
        try {
            const data = JSON.stringify(task);
            await redisPublisher.lpush(this.chatQueue, data);
        } catch (err) {
            console.error('[Redis] lỗi push embedding task', err);
            throw err;
        }

    }
// cache 

    async getCache(key){
        const data = await redisPublisher.get(key)
        return data || null 
    }

    async setCache(key,value,ttl =3600){
        await redisPublisher.set(key,value,'EX',ttl)
    }
    async delCache(key) {
        await redisPublisher.del(key);
        console.log(`[Cache] Đã xóa key: ${key}`);
    }

    // end cache redis 
}

module.exports = new RedisService();