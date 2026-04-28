const express = require("express")
const router = express.Router()
const promptController = require('../../controllers/Admin/promt.controller')
const SummaryPromptController = require('../../controllers/Admin/summaryPrompt.controller')
router.patch('/edit/:id',promptController.edit)
router.get('/group',promptController.group)
router.post('/SummaryPrompt/create',SummaryPromptController.create)
router.patch('/SummaryPrompt/edit/:promptId',SummaryPromptController.edit)
router.get("/SummaryPrompt/list",SummaryPromptController.list)

module.exports = router