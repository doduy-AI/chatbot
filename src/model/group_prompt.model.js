const {DataTypes} = require('sequelize')
const sequelize = require('../config/db')

const prompt = sequelize.define('prompt',{
     id:{
        type: DataTypes.UUID,
        defaultValue: DataTypes.UUIDV4,
        primaryKey: true,
        allowNull: false
    },
    groupId:{
        type:DataTypes.UUID,
        allowNull:false,
        references:{
            model:"Groups",
            key:"groupId"
        }
    },
    promptName:{
        type:DataTypes.STRING,
        allowNull:false,
    },
    content: {
        type: DataTypes.TEXT, 
        allowNull: false,
    },
    
},
{
    timestamps: true
})
module.exports = prompt