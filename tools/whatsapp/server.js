const express = require('express');
const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode');
const fs = require('fs');
const path = require('path');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 3001; // Mudado para 3001 para evitar conflito com React

app.use(express.json());
app.use(cors());

// Status
let isReady = false;
let qrCodeUrl = null;

// Detecção de Navegador (Chrome ou Edge)
// const fs = require('fs'); <- REMOVIDO (Já importado no topo)
let executablePath = null;
const possiblePaths = [
    'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
    'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe',
    'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
];

for (const p of possiblePaths) {
    if (fs.existsSync(p)) {
        executablePath = p;
        console.log(`[WHATSAPP] Usando navegador do sistema: ${p}`);
        break;
    }
}

// Inicializar Cliente WhatsApp
const client = new Client({
    authStrategy: new LocalAuth({ dataPath: './session' }),
    authTimeoutMs: 60000,

    // Forçar versão mais recente do Zap Web para evitar conflito
    webVersionCache: {
        type: 'remote',
        remotePath: 'https://raw.githubusercontent.com/wppconnect-team/wa-version/main/html/2.2412.54.html',
    },

    puppeteer: {
        executablePath: executablePath, // Usa o navegador real se achar
        headless: true,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--no-first-run',
            '--no-zygote',
            '--disable-gpu',
            // Camuflagem de Bot 🥷
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        ]
    }
});

client.on('loading_screen', (percent, message) => {
    console.log('[WHATSAPP] Carregando:', percent, '% -', message);
});

// Eventos
client.on('qr', (qr) => {
    console.log('[WHATSAPP] QR Code recebido! Gere a imagem para escanear.');
    qrCodeUrl = qr;
    isReady = false;

    // Gerar imagem do QR Code na raiz do projeto tools/whatsapp
    qrcode.toFile('./whatsapp-qr.png', qr, (err) => {
        if (err) console.error('[WHATSAPP] Erro ao salvar QR:', err);
        else console.log('[WHATSAPP] QR Code salvo em whatsapp-qr.png. Abra este arquivo para escanear!');
    });
});

client.on('ready', () => {
    console.log('[WHATSAPP] Cliente conectado e pronto!');
    isReady = true;
    qrCodeUrl = null;
    // Apagar o QR code se existir
    if (fs.existsSync('./whatsapp-qr.png')) {
        fs.unlinkSync('./whatsapp-qr.png');
    }
});

client.on('authenticated', () => {
    console.log('[WHATSAPP] Autenticado com sucesso!');
});

client.on('auth_failure', msg => {
    console.error('[WHATSAPP] Falha na autenticação:', msg);
});

// API Endpoints

// 1. Status
app.get('/status', (req, res) => {
    res.json({
        ready: isReady,
        qr_code_available: !!qrCodeUrl
    });
});

// 2. Enviar Mensagem
app.post('/send', async (req, res) => {
    if (!isReady) {
        return res.status(503).json({ error: 'WhatsApp ainda não está conectado/pronto.' });
    }

    const { number, message } = req.body;

    if (!number || !message) {
        return res.status(400).json({ error: 'Número e mensagem são obrigatórios.' });
    }

    try {
        // Formatar número (Brasil)
        // Se vier apenas números, tenta formatar para 55DDD...
        let formattedNumber = number.replace(/\D/g, '');

        if (!formattedNumber.endsWith('@c.us')) {
            if (formattedNumber.length <= 11) {
                formattedNumber = '55' + formattedNumber;
            }
            formattedNumber += '@c.us';
        }

        const response = await client.sendMessage(formattedNumber, message);
        res.json({ success: true, id: response.id._serialized });
        console.log(`[WHATSAPP] Mensagem enviada para ${number}`);

    } catch (error) {
        console.error('[WHATSAPP] Erro ao enviar mensagem:', error);
        res.status(500).json({ error: error.message });
    }
});

// Rota para listar Grupos (Blindada)
app.get('/groups', async (req, res) => {
    console.log("[API] Solicitando lista de grupos...");

    if (!isReady) {
        return res.status(503).json({ error: 'WhatsApp ainda conectando... Aguarde o status "Ready".' });
    }

    try {
        const chats = await client.getChats();
        // Filtra só grupos
        const groups = chats
            .filter(chat => chat.isGroup)
            .map(chat => ({
                name: chat.name,
                id: chat.id._serialized
            }));

        console.log(`[API] Encontrados ${groups.length} grupos.`);
        res.json(groups);
    } catch (error) {
        console.error("Erro CRÍTICO ao listar grupos:", error);
        res.status(500).json({ error: 'Falha interna ao buscar chats. O WhatsApp pode estar sincronizando.', details: error.toString() });
    }
});

// Inicializar Servidor
app.listen(PORT, () => {
    console.log(`[GATEWAY] Servidor API WhatsApp rodando na porta ${PORT}`);
    console.log(`[GATEWAY] Iniciando cliente WhatsApp Web... aguarde.`);
    client.initialize();
});
