const listUser = (req,res)=>{
    console.log(req.user)
    res.json({
        message:"list user"
    })
}


const create = (req,res)=>{
    console.log(req.user)
    res.json({
        message:"list user"
    })
}

const update = (req,res)=>{
    console.log(req.user)
    res.json({
        message:"list user"
    })
}


module.exports = {listUser ,create ,update}