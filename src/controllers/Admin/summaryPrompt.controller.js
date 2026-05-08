const SummaryPrompt = require('../../model/summary_prompt.model')
const Prompt = require('../../model/group_prompt.model')

const create = async (req,res)=>{
    try { 
        const {promptId , summary_prompt } = req.body

        if (!promptId){
            return res.status(404).json({message: "Không có promptID "})
        }

        const exisPrompt = await Prompt.findOne({
                where: { id: promptId }
            });
        if (!exisPrompt) {
                return res.status(404).json({ message: "Prompt gốc không tồn tại!" });
            }
        
        const newSummary = await SummaryPrompt.create({
            promptId,
            summary_prompt
        })

        return res.status(200).json({
            message: "Thêm thành công Summary Prompt ",
            data: newSummary
        })
            

        } catch (err){
            return res.status(500).json({ error: error.message });
        }
   
}

const edit = async(req,res)=>{
    try {
        const { promptId } = req.params; 
        const { summary_prompt } = req.body;
        console.log(promptId)
        if (!promptId){
            return res.status(404).json({
                message:  "Thiếu promptId"
            })
        }
        const exisPromptId = await SummaryPrompt.findOne({
            where:{id: promptId}
        })

        if (!exisPromptId){
            return res.status(404).json({
                message: "Không tồn tại promptId"
            })
        }

        const updateData = await SummaryPrompt.update({
            summary_prompt: summary_prompt
        },
        {
            where:{
                promptId:promptId
            }
        })
        
        if (updateData === 0 ) {    
            return res.status(404).json({message: "Không tìm thấy bản ghi"})  
        }
        return res.status(200).json({message: "Update thành công" })
        
    } catch (err) {
        return res.status(500).json({
            message:err
        })
    }
}

const list = async (req, res)=> {
    try {
        const data = await SummaryPrompt.findAll({
            order: [['createdAt', 'DESC']]
        })
        return res.status(200).json({
            message:"Lấy data thành công ",
            count:data.length,
            data:data
        })
    } catch (error) {
        return res.status(500).json({message: error})
    }
}


module.exports = {create, edit , list}