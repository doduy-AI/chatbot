const express = require('express');
const router = express.Router();
const ragController = require('../controllers/rag.controller');

router.post('/uploadfile', ragController.uploadfile);



module.exports = router;