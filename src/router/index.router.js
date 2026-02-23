const auth = require('./auth.router')

module.exports = (app) => {
  app.use("/auth",auth)
}