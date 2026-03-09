const express = require('express')
const router = express.Router()
const groupController = require('../../controllers/Admin/group.controller')

router.post('/create',groupController.create)

module.exports =router