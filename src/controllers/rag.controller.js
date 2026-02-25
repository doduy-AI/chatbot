const uploadfile = async (req, res) => {
    try {
    console.log('🧾 Body:', req.body);
    console.log('📂 Files:', req.files);

    const userId = req.user.id;
    const files = req.files;

    if (!userId) return res.status(400).json({ success: false, message: 'Thiếu userId!' });
    if (!files || files.length === 0)
      return res.status(400).json({ success: false, message: 'Chưa chọn file nào!' });

    // Nếu có DB thì thử comment phần này lại để test
    // await File.insertMany(...);

    res.json({
      success: true,
      message: 'Upload thành công!',
      userId,
      files: files.map(f => ({
        filename: f.filename,
        path: f.path,
        size: f.size
      }))
    });
  } catch (error) {
    console.error('🔥 Lỗi upload:', error);
    res.status(500).json({ success: false, message: 'Internal Server Error', error: error.message });
  }
};

module.exports = { uploadfile };