const Redis = require('ioredis')
const config = require("../config/server")


const redisPublisher = new Redis({
    host:config.HOST_REDIS,
    port:config.PORT_REDIS
})

const redisSubscriber = new Redis({
    host:config.HOST_REDIS,
    port:config.PORT_REDIS
})

class RedisService{
    constructor(){
        this.queueName = 'ai_tasks';
        this.responseChannel = 'ai_responses';
    }
    async pushTask(task){
        try {
            const data = JSON.stringify(task)
            await redisPublisher.lpush(this.queueName, data);
        } catch (err) {
            console.error('[Redis] lỗi push task ' , err)
            throw err
        }
    }
    listenForResponses(callback) {
        redisSubscriber.subscribe(this.responseChannel);
        
        redisSubscriber.on('message', (channel, message) => {
            if (channel === this.responseChannel) {
                const data = JSON.parse(message);
                callback(data);
            }
        });
    }
}

module.exports = new RedisService();