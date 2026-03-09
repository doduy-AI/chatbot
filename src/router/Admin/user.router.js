const express = require('express')
const router = express.Router()
const userController = require('../../controllers/Admin/user.controller')

router.get('/list',userController.listUser)

// router.post('/create')


module.exports =router;