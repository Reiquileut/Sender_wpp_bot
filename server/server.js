// server.js - Servidor WhatsApp Simplificado
const express = require('express');
const { Client, LocalAuth, MessageMedia } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const fs = require('fs');
const multer = require('multer');
const cors = require('cors');
const bodyParser = require('body-parser');

const app = express();
const port = 3000;

// Configuração do diretório para armazenar arquivos temporários
const upload = multer({ dest: 'uploads/' });

// Middleware
app.use(cors());
app.use(bodyParser.json());
app.use(express.static('public'));

// Variáveis globais
let clientReady = false;
let qrData = null;

// Inicializa o cliente WhatsApp
const client = new Client({
    authStrategy: new LocalAuth({
        dataPath: './whatsapp-session'
    }),
    puppeteer: {
        headless: true,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--disable-gpu'
        ]
    }
});

// Evento quando o QR code é recebido
client.on('qr', (qr) => {
    qrData = qr;
    qrcode.generate(qr, { small: true });
    console.log('QR Code gerado. Escaneie-o com seu WhatsApp.');
});

// Evento quando o cliente está pronto
client.on('ready', () => {
    clientReady = true;
    qrData = null;
    console.log('Cliente WhatsApp está pronto!');
});

// Evento de autenticação
client.on('authenticated', () => {
    console.log('Autenticado com sucesso!');
});

// Evento de desconexão
client.on('disconnected', (reason) => {
    clientReady = false;
    console.log('Cliente desconectado:', reason);
    // Reinicializa o cliente após um tempo
    setTimeout(() => client.initialize(), 5000);
});

// Inicializa o cliente
client.initialize();

// Rota para verificar o status do cliente
app.get('/api/status', (req, res) => {
    res.json({
        ready: clientReady,
        qrCode: qrData ? true : false
    });
});

// Rota para obter o QR code
app.get('/api/qrcode', async (req, res) => {
    if (!qrData) {
        return res.status(404).json({ error: 'QR Code não disponível' });
    }
    
    try {
        // Retorna o texto do QR code
        res.json({ qrCodeText: qrData });
    } catch (error) {
        res.status(500).json({ error: 'Erro ao gerar QR Code' });
    }
});

// Rota para enviar mensagem de texto
app.post('/api/send-message', async (req, res) => {
    const { number, message } = req.body;
    
    if (!clientReady) {
        return res.status(400).json({ error: 'Cliente WhatsApp não está pronto' });
    }
    
    if (!number || !message) {
        return res.status(400).json({ error: 'Número e mensagem são obrigatórios' });
    }
    
    try {
        // Formata o número para o padrão internacional
        const formattedNumber = formatPhoneNumber(number);
        
        // Envia a mensagem
        const result = await client.sendMessage(`${formattedNumber}@c.us`, message);
        res.json({ success: true, messageId: result.id._serialized });
    } catch (error) {
        console.error('Erro ao enviar mensagem:', error);
        res.status(500).json({ error: 'Erro ao enviar mensagem', details: error.message });
    }
});

// Rota para enviar arquivo
app.post('/api/send-file', upload.single('file'), async (req, res) => {
    const { number } = req.body;
    const caption = req.body.caption || '';
    
    if (!clientReady) {
        return res.status(400).json({ error: 'Cliente WhatsApp não está pronto' });
    }
    
    if (!number || !req.file) {
        return res.status(400).json({ error: 'Número e arquivo são obrigatórios' });
    }
    
    try {
        // Formata o número para o padrão internacional
        const formattedNumber = formatPhoneNumber(number);
        
        // Caminho do arquivo
        const filePath = req.file.path;
        const fileName = req.file.originalname;
        
        // Envia o arquivo
        const media = MessageMedia.fromFilePath(filePath);
        media.filename = fileName;
        
        const result = await client.sendMessage(`${formattedNumber}@c.us`, media, { caption });
        
        // Remove o arquivo temporário
        fs.unlinkSync(filePath);
        
        res.json({ success: true, messageId: result.id._serialized });
    } catch (error) {
        console.error('Erro ao enviar arquivo:', error);
        // Tenta limpar o arquivo temporário em caso de erro
        if (req.file && req.file.path) {
            try {
                fs.unlinkSync(req.file.path);
            } catch (e) {
                console.error('Erro ao remover arquivo temporário:', e);
            }
        }
        res.status(500).json({ error: 'Erro ao enviar arquivo', details: error.message });
    }
});

// Função para formatar número de telefone
function formatPhoneNumber(number) {
    // Remove todos os caracteres que não são dígitos
    let cleaned = number.replace(/\D/g, '');
    
    // Adiciona o código do país (Brasil) se não existir
    if (cleaned.length <= 11) {
        cleaned = '55' + cleaned;
    } else if (cleaned.startsWith('55') && cleaned.length > 13) {
        // Ajusta números com formato incorreto
        cleaned = '55' + cleaned.substring(2, 13);
    }
    
    return cleaned;
}

// Inicia o servidor
app.listen(port, () => {
    console.log(`Servidor rodando em http://localhost:${port}`);
});