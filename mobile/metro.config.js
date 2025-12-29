const { getDefaultConfig } = require('expo/metro-config');
const { createProxyMiddleware } = require('http-proxy-middleware');

const config = getDefaultConfig(__dirname);

config.server = {
    ...config.server,
    enhanceMiddleware: (middleware) => {
        return (req, res, next) => {
            if (req.url.startsWith('/api')) {
                return createProxyMiddleware({
                    target: 'http://localhost:8080',
                    changeOrigin: true,
                    secure: false,
                    logLevel: 'debug',
                    onProxyReq: (proxyReq, req, res) => {
                        // Log para debug
                        console.log(`[PROXY] ${req.method} ${req.url} -> Backend`);
                    },
                    onError: (err, req, res) => {
                        console.error('[PROXY ERROR]', err.message);
                        res.writeHead(500, {
                            'Content-Type': 'text/plain',
                        });
                        res.end('Proxy Error: ' + err.message);
                    }
                })(req, res, next);
            }
            return middleware(req, res, next);
        };
    },
};

module.exports = config;
