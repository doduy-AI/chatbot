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
    roleid:{
            type:DataTypes.INTEGER,
            allowNull:false,
            references:{
                model:"Role",
                key:"roleid"
            }
    },
    groupId:{
        type:DataTypes.UUID,
        allowNull:false,
        references:{
            model:"Groups",
            key:"groupId"
        }
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
    // hooks: {
    //     beforeBulkCreate: async (user) => {
    //         console.log(user)
    //         const salt = await bcrypt.genSalt(10);
    //         user.password = await bcrypt.hash(user.password , salt)
    //     }
    // }
})

module.exports = User ;