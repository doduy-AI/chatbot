const express = require('express')
const router =express.Router()
const {verifyToken} = require('../../middlewares/authAPI.middleware')
const upload = require('../../config/multer.config')
const chat =require('../../controllers/client/chat.controller')
const ragController = require('../../controllers/client/rag.controller')
router.use(verifyToken)
router.post('/rag/uploadfile',upload.array('files', 10),ragController.uploadfile)
router.post('/chat',chat.chat)

module.exports = router