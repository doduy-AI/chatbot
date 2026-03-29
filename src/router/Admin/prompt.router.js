const express = require("express")
const router = express.Router()
const promptController = require('../../controllers/Admin/promt.controller')

router.patch('/edit/:id',promptController.edit)
router.get('/group',promptController.group)

module.exports = router