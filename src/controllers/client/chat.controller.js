const redisService = require('../../services/redisService');
const User = require('../../model/user.model')
const Prompt = require('../../model/group_prompt.model')


const chat = async(req,res)=>{
        try {
            const userId = req.user.id
            if (!userId) return res.status(400).json({ success: false, message: 'Thiếu userId!' });
            const user = await User.findOne({
                where:{
                    id:userId,
                }
            })
            const userID = req.user.id
            const groupId = user.groupId
            

            const cacheKey = `group:${groupId}:content`;
            let content = await redisService.getCache(cacheKey)
            if (!content) {
                console.log(`[Cache HIT] group ${groupId}`);

                    const promptGroup = await Prompt.findOne({
                    where:{
                        groupId:groupId
                    }
                })
                content = promptGroup.content 
                await redisService.setCache(cacheKey, content, 3600);
                console.log(`[Cache MISS] group ${groupId} → đã lưu cache`);
            }
            const {  text, history} = req.body 
            const service = "chat"
            const job ={
                userId,
                groupId,
                text,
                service  
            } 
            await redisService.pushTask(job)
            
            await redisService.pushTask(job)

            const reply = await new Promise((resolve, reject) => {
                const timeout = setTimeout(() => reject(new Error("Timeout")), 30000);
                
                redisService.listenForResponsesChat((resUserId, data) => {
                    if (resUserId === userId) { 
                        clearTimeout(timeout);
                        resolve(data);
                    }
                });
            });

            return res.status(200).json({
                success: true,
                reply: reply.reply
            });
        } catch (error) {
            res.status(500).json({ success: false, message: 'Internal Server Error', error: error.message });
        }
}

module.exports = {chat}