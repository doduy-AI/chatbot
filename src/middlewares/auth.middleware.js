const config = require('../config/server')

const veryConnection = (info, cb) => {
    const url = new URL(info.req.url, `http://${info.req.headers.host}`);
    const token = url.searchParams.get('token');
}