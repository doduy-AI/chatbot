const multer = require('multer');
const path = require('path');
const fs = require('fs');


const slugify = (str) => {
  return str
    .toLowerCase()
    .normalize('NFD')                 // Tách dấu khỏi chữ cái
    .replace(/[\u0300-\u036f]/g, '') // Xóa các dấu vừa tách
    .replace(/[đĐ]/g, 'd')           // Xử lý riêng chữ đ
    .replace(/[^a-z0-9\s.-]/g, '')   // Xóa ký tự đặc biệt trừ dấu chấm và gạch ngang
    .replace(/\s+/g, '-')            // Thay khoảng trắng bằng dấu gạch ngang
    .replace(/-+/g, '-');            // Loại bỏ nhiều gạch ngang liên tiếp
};


const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    const userId = req.user.id || 'unknown_user';
    console.log(userId)

    // Tạo thư mục theo userId
    const uploadPath = path.join('uploads', userId);
    fs.mkdirSync(uploadPath, { recursive: true });

    cb(null, uploadPath);
  },
  filename: (req, file, cb) => {
    const ext = path.extname(file.originalname);
    const originalNameOnly = path.basename(file.originalname, ext);
    const slugName = slugify(originalNameOnly);
    const finalName = `${Date.now()}-${slugName}${ext}`;
    cb(null, finalName);
  }
});

const upload = multer({ storage });

module.exports = upload;