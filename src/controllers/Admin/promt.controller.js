
const { JSON } = require('sequelize');
const { Group, Prompt } = require('../../model/index'); // file chứa association

const create = async (req,res)=>{
  try {
        const {groupId , promptName ,content} = req.body
        const existPromt = await Prompt.findOne({
            where:{
                groupId:groupId
            }
        })
        // console.log(existPromt)
        if(existPromt){
            return res.status(400).json({
                success:false,
                message:"user này đã có prompt rồi "
            })
        }

        const newPrompt = await Prompt.create({
                groupId,
                promptName,
                content
            });

            return res.status(201).json({
                success: true,
                data: newPrompt
            });

  } catch (error) {
        return res.status(500).json({
            success:false,
            message:error.message
        })
  }

}

const edit = async(req,res) => {
    console.log("oke")
}

const group = async(req,res) =>{
    try {
        const data  = await Group.findAll({
            attributes:['groupId','groupName'],
            include:[{
                model:Prompt,
                as:'prompt',
                attributes:['id','promptName','content']
                
            }],
            // logging: console.log
        })

        const result = data.map(item => item.toJSON())
        res.status(200).json(result)

} catch (error) {
        console.error("Lỗi Controller:", error);
        res.status(500).send(error.message);
    }
}

module.exports = {create,edit,group}