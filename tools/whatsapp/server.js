const express = require('express');
const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode');
const fs = require('fs');
const path = require('path');
const cors = require('cors');

// Load environment variables from .env file
require('dotenv').config({ path: path.join(__dirname, '..', '..', '.env') });

const app = express();
const PORT = process.env.PORT || 3001; // Mudado para 3001 para evitar conflito com React

app.use(express.json());
app.use(cors());

// --- SECURITY: API KEY PROTECTION ---
const MSG_SECRET = process.env.MSG_SECRET || "msg-secret-key";

// Middleware to protect private endpoints
const authMiddleware = (req, res, next) => {
    // Public endpoints
    if (req.path === '/status' || req.path === '/qr') return next();

    const token = req.headers['x-api-key'];
    if (token !== MSG_SECRET) {
        return res.status(403).json({ error: 'Acesso negado: API Key inválida' });
    }
    next();
};

app.use(authMiddleware);

// Status
let isReady = false;
let qrCodeUrl = null;

// Detecção de Navegador (Chrome ou Edge)
// const fs = require('fs'); <- REMOVIDO (Já importado no topo)
let executablePath = null;
const possiblePaths = [
    // 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    // 'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe', 
    // ... Disabled to force Bundled Chromium (More stable with Puppeteer)
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

    // Travando em versão estavel (Fev 2024) para evitar LIDs bugs da nova versao
    /*
    webVersionCache: {
        type: 'remote',
        remotePath: 'https://raw.githubusercontent.com/wppconnect-team/wa-version/main/html/2.2407.3.html',
    },
    */

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
            '--no-zygote',
            '--disable-gpu',
            '--disable-web-security', // Fix for "Execution context destroyed" injection fail
            // Camuflagem de Bot 🥷
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        ],
        bypassCSP: true, // Importante para evitar erros de injeção em versões novas
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
        try {
            fs.unlinkSync('./whatsapp-qr.png');
        } catch (e) {
            console.error('[WHATSAPP] Erro ao limpar QR code:', e.message);
        }
    }

    // CRIAR ARQUIVO DE SINAL PARA O LAUNCHER
    try {
        fs.writeFileSync('./whatsapp_is_ready.txt', 'READY');
    } catch (e) {
        console.error('[WHATSAPP] Erro ao criar arquivo de sinal:', e.message);
    }
});

client.on('disconnected', () => {
    console.log('[WHATSAPP] Cliente desconectado!');
    isReady = false;
    if (fs.existsSync('./whatsapp_is_ready.txt')) {
        try {
            fs.unlinkSync('./whatsapp_is_ready.txt');
        } catch (e) { }
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

// Novo Endpoint para retornar o QR Code bruto
app.get('/qr', (req, res) => {
    if (qrCodeUrl) {
        res.json({ qr: qrCodeUrl });
    } else {
        res.status(404).json({ error: 'QR Code não disponível (Cliente já está conectado ou iniciando).' });
    }
});

// 2. Enviar Mensagem
app.post('/send', async (req, res) => {
    try {
        const { number, message } = req.body;
        console.log(`[API /send] Recebido: Target='${number}', Message='${message}'`);

        if (!number || !message) {
            return res.status(400).json({ error: 'Número e mensagem são obrigatórios' });
        }

        if (!isReady) {
            return res.status(503).json({ error: 'WhatsApp ainda não está pronto.' });
        }

        let chatId = number.trim();

        // Lógica inteligente de ID
        if (chatId.includes('@g.us')) {
            console.log(`[API /send] Detectado GRUPO: ${chatId}`);
            // É um grupo, confiar no ID passado
        } else if (chatId.includes('@c.us')) {
            // Já tem sufixo de contato
        } else {
            // É apenas número telefônico -> Formatar
            let cleanNumber = chatId.replace(/\D/g, '');
            // Brasil: Adicionar 55 se estiver sem DDI e tiver tamanho de DDD+CEL (10 ou 11)
            if (cleanNumber.length >= 10 && cleanNumber.length <= 11) {
                cleanNumber = '55' + cleanNumber;
            }
            chatId = cleanNumber + '@c.us';
        }

        // Se for contato, verificar validação. Se for grupo, tenta enviar direto.
        if (chatId.includes('@c.us')) {
            const user = await client.getNumberId(chatId.split('@')[0]);
            if (!user) {
                console.warn(`[API /send] Número inválido/não registrado: ${chatId}`);
                return res.status(404).json({ error: 'Número não registrado no WhatsApp.' });
            }
            chatId = user._serialized;
        }

        console.log(`[API /send] Enviando para: ${chatId}`);
        const response = await client.sendMessage(chatId, message);

        res.json({ success: true, id: response.id._serialized, target: chatId });
        console.log(`[WHATSAPP] Mensagem enviada com sucesso para ${chatId}`);

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
app.listen(PORT, async () => {
    console.log(`[GATEWAY] Servidor API WhatsApp rodando na porta ${PORT}`);

    // Limpar arquivo de flag antigo
    if (fs.existsSync('./whatsapp_is_ready.txt')) {
        try { fs.unlinkSync('./whatsapp_is_ready.txt'); } catch (e) { }
    }

    console.log(`[GATEWAY] Iniciando cliente WhatsApp Web... aguarde.`);

    // Auto-fix: Se houver erro de injeção/protocolo crítico (Execution context destroyed),
    // limpamos a sessão e reiniciamos automaticamente.
    try {
        await client.initialize();
    } catch (err) {
        console.error('[WHATSAPP] 💥 Erro Fatal na Inicialização:', err.message);
        if (err.message.includes('Protocol error') || err.message.includes('context was destroyed')) {
            console.warn('[WHATSAPP] 🧹 Detectada sessão corrompida. Limpando para auto-reparo...');
            const sessionPath = path.join(__dirname, 'session');
            if (fs.existsSync(sessionPath)) {
                try {
                    fs.rmSync(sessionPath, { recursive: true, force: true });
                    console.log('[WHATSAPP] ✨ Sessão limpa. O sistema tentará gerar um novo QR Code no próximo início.');
                    process.exit(1); // Sai para o Self-Heal reiniciar o processo do zero
                } catch (e) {
                    console.error('[WHATSAPP] Falha ao limpar sessão:', e.message);
                    // Não sai do processo se falhar o delete, tenta continuar ou avisa
                }
            }
        }
    }
});
