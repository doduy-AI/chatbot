const express = require('express')
const router = express.Router()
const {verifyToken ,isAdmin} = require('../../middlewares/authAPI.middleware')

const user = require('./user.router')

router.use('/user' ,verifyToken ,isAdmin,user)

module.exports = router