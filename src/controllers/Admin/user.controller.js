const User = require('../../model/user.model')
const bcrypt = require('bcryptjs');

const listUser = (req,res)=>{
    console.log(req.user)
    res.json({
        message:"list user"
    })
}


const create = async(req,res)=>{
    try{
       const {groupId , username , password }  = req.body
       console.log(username)
       const existingUser = await User.findOne({where:{username}})
       if(existingUser){
        return res.status(400).json({
            success:false,
            message:'username da ton tai'
        })
       }

       const salt = await bcrypt.genSalt(10)

       const hashedPassword = await bcrypt.hash(password,salt)

       const userNew = await User.create({
        roleid:"1",
        groupId:groupId,
        username:username,
        password:hashedPassword
       })

       res.status(200).json({
        success:true,
        message:"them thanh cong user",
        data:{
            id:userNew.id,
            roleid:userNew.roleid,
            groupId:userNew.groupId,
            username:userNew.username
        }
       })



    }
    catch(e){
        return res.status(500).json({
            success:false,
            message:e.message
        })
    }
}

const update = (req,res)=>{
    console.log(req.user)
    res.json({
        message:"list user"
    })
}


module.exports = {listUser ,create ,update}