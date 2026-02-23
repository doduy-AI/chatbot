const express = require('express');
const router = express.Router();

router.get('/', (req, res) => {
  res.json({ message: 'API hoạt động tốt ' });
});

module.exports = router;