// ✅ src/middlewares/auth.middleware.js
const config = require('../config/server');
const jwt = require('jsonwebtoken');

const verifyToken = (req, res, next) => {
  const authHeader = req.headers['authorization'];
  if (!authHeader)
    return res.status(401).json({ message: 'Thiếu token' });

  const token = authHeader.split(' ')[1];
  try {
    const decoded = jwt.verify(token, config.AUTH_TOKEN);
    req.user = decoded;
    next();
  } catch (err) {
    return res.status(403).json({ message: 'Token không hợp lệ hoặc đã hết hạn' });
  }
};

module.exports = verifyToken; // 👈 export trực tiếp function