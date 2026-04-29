const { QueryTypes } = require('sequelize');
const sequelize = require('../config/db');

const findSummaryByGroupId = async (groupId) => {
    const sql = `
        SELECT sp.* FROM "SummaryPrompts" sp
        INNER JOIN "prompts" p ON sp."promptId" = p."id"
        WHERE p."groupId" = :groupId
        LIMIT 1
    `;
    
    const results = await sequelize.query(sql, {
        replacements: { groupId },
        type: QueryTypes.SELECT
    });

    return results[0] || null;
};

module.exports = {
    findSummaryByGroupId};