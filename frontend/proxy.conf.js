
const PROXY_HOST = 'https://opendataqna-kdr33rftkq-uc.a.run.app';

const PROXY_CONFIG = [{
    context: ['/mp'],
    "target": PROXY_HOST,
    "secure": true,
}]

module.exports = PROXY_CONFIG