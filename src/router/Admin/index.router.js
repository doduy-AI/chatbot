const express = require('express')
const router = express.Router()
const {verifyToken ,isAdmin} = require('../../middlewares/authAPI.middleware')
const user = require('./user.router')
const group = require('./group.router')
router.use(verifyToken,isAdmin)


router.use('/user' ,user)
router.use('/group',group)

module.exports = router