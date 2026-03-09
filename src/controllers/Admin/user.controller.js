const listUser = (req,res)=>{
    console.log(req.user)
    res.json({
        message:"list user"
    })
}

module.exports = {listUser}