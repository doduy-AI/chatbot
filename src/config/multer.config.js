const multer = require('multer');
const path = require('path');
const fs = require('fs');

const slugify = (str) => {
  return str
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[đĐ]/g, 'd')
    .replace(/[^a-z0-9\s-]/g, '')   
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .trim();
};

const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    const userId = (req.user && req.user.id) ? req.user.id : 'unknown_user';
    const uploadPath = path.join('uploads', userId);
    
    if (!fs.existsSync(uploadPath)) {
      fs.mkdirSync(uploadPath, { recursive: true });
    }

    cb(null, uploadPath);
  },
  filename: (req, file, cb) => {
    const ext = path.extname(file.originalname).toLowerCase(); 
    const originalNameOnly = path.basename(file.originalname, ext);
    const slugName = slugify(originalNameOnly);
    const finalName = `${Date.now()}-${slugName}${ext}`;
    cb(null, finalName);
  }
});

const upload = multer({ storage });

module.exports = upload;