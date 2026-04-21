const redisService = require('../../services/redisService');
const User = require('../../model/user.model')

const chat = async(req,res)=>{
        const userId = req.user.id
        if (!userId) return res.status(400).json({ success: false, message: 'Thiếu userId!' });
        const user = await User.findOne({
            where:{
                id:userId,
            }
        })
        const userID = req.user.id
        const groupId = user.groupId
        const {  text, history} = req.body 
        const job ={
           userID,
           groupId,
           text
        } 
        console.log(job)
}

module.exports = {chat}