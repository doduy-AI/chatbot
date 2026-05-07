const {DataTypes} = require('sequelize')
const sequelize = require('../config/db')

const SummaryPrompt = sequelize.define('SummaryPrompt',{
    id:{
        type: DataTypes.UUID,
        defaultValue: DataTypes.UUIDV4 ,
        primaryKey: true,
        allowNull: false
    },
    promptId:{
        type:DataTypes.UUID,
        allowNull:false,
        unique:true,
        references:{
            model:"prompts",
            key:"id"
        },
        onDelete:'CASCADE'
    },
    summary_prompt:{
        type:DataTypes.TEXT,
        allowNull:false
    }
},{
    timestamps:true
}) 

module.exports = SummaryPrompt