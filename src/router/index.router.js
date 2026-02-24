const auth = require('./auth.router')
const rag = require('./rag.router')

module.exports = (app) => {
  app.use("/auth",auth)
  app.use("/rag",rag)
}