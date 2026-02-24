const express = require('express');
const router = express.Router();
const ragController = require('../controllers/rag.controller');
const verifyToken = require("../middlewares/authAPI.middleware"); // 👈 tên trùng export ở trên


router.post('/uploadfile', verifyToken ,ragController.uploadfile);

module.exports = router;