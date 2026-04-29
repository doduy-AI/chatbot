const { Json } = require('sequelize/lib/utils');
const SummaryRepo = require('../repositories/summaryPrompt.repository')
const redis = require('./redisService')

const getSummaryWithCache = async (groupId) => {
    try {
        const sumary_prompt = SummaryRepo(groupId)
        const summary_prompt_id = sumary_prompt.id
        const sumary_prompt_content = sumary_prompt.summary_prompt
        console.log(summary_prompt_id,sumary_prompt_content)
    } catch (error) {
        
    }


}

module.exports = { getSummaryWithCache };