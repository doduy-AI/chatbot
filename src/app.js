require('dotenv').config(); 
const express = require('express');
const http = require('http');
const sequelize = require('./config/db'); 
const routes = require('./router/index.router');   
const serverConfig = require('./config/server');

const app = express();
const server = http.createServer(app); 
const User = require('./model/user.model');


app.use(express.json());
app.use(express.urlencoded({ extended: true }));


const router = require("./router/index.router")
router(app)

app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).json({ success: false, message: 'Internal Server Error' });
});


sequelize
  .authenticate()
  .then(() => {
    console.log('Kết nối database thành công!');
    // alter: true giúp cập nhật bảng khi bạn đổi Model mà không xóa data
    return sequelize.sync({ alter: true }); 
  })
  .then(() => {
    console.log(' Đã sync models!');
    const PORT = serverConfig.PORT || 3000;
    
    server.listen(PORT, () => {
      console.log(` Server đang chạy tại http://localhost:${PORT}`);
    });
  })
  .catch((err) => {
    console.error(' Lỗi kết nối hoặc sync database:', err.message);
    process.exit(1); 
  });