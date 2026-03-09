const Role = require("./role.model")
const Group = require("./group.model")
const User = require("./user.model")

const sequelize = require('../config/db');

// Một quyền thuộc về nhiều user (1-N)
Role.hasMany(User,{
    foreignKey:"roleid"
})

// một user chỉ có 1 quyền duy nhất 
User.belongsTo(Role,{
    foreignKey:"roleid"
})

// một group thif có nhiều user 
Group.hasMany(User,{
    foreignKey:"groupId"
})

User.belongsTo(Group,{
    foreignKey:"groupId"
})


module.exports = { 
    sequelize ,
    Role,
    Group,
    User
}


