const uploadfile = async (req, res) => {
    console.log("đã chạy vào đây")
    res.status(201).json({
            success: true,
            message: 'Đăng ký thành công!',
        });
}

module.exports = { uploadfile };