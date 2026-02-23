const {DataTypes} = require('sequelize')
const sequelize = require('../config/db')
const bcrypt = require('bcryptjs')

const User = sequelize.define('User',{
    id:{
        type: DataTypes.UUID,
        defaultValue: DataTypes.UUIDV4,
        primaryKey: true,
        allowNull: false
    },
    username:{
        type: DataTypes.STRING,
        allowNull:false,
        unique:true
    },
    password:{
        type: DataTypes.STRING,
        allowNull:false
    }
},{
    timestamps: true,
    hooks: {
        beforeBulkCreate: async (user) => {
            const salt = await bcrypt.genSalt(10);
            user.password = await bcrypt.hash(user.password , salt)
        }
    }
})

module.exports = User ;