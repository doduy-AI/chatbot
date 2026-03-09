const auth = require('./auth.router')
const rag = require('./rag.router')
const admin = require("./Admin/index.router")
module.exports = (app) => {
  app.use("/auth",auth)
  app.use("/rag",rag)
  app.use("/api/admin",admin)


}