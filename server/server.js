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

// Lista de códigos de país comuns e seus tamanhos de número
const countryCodes = {
    '1': { name: 'EUA/Canadá', lengths: [10] }, // EUA/Canadá: +1 e 10 dígitos
    '44': { name: 'Reino Unido', lengths: [10] }, // Reino Unido: +44 e 10 dígitos
    '351': { name: 'Portugal', lengths: [9] }, // Portugal: +351 e 9 dígitos
    '55': { name: 'Brasil', lengths: [10, 11] }, // Brasil: +55 e 10-11 dígitos (com/sem DDD)
    '61': { name: 'Austrália', lengths: [9, 10] }, // Austrália: +61 e 9-10 dígitos
    '81': { name: 'Japão', lengths: [10, 11] }, // Japão: +81 e 10-11 dígitos
};

// Função melhorada para formatar número de telefone internacional
function formatPhoneNumber(number) {
    // Remove todos os caracteres que não são dígitos
    let cleaned = number.replace(/\D/g, '');
    
    // Verifica se o número já começa com um código de país conhecido
    let countryCode = null;
    for (const code in countryCodes) {
        if (cleaned.startsWith(code)) {
            countryCode = code;
            break;
        }
    }
    
    // Se não tiver código de país, tenta identificar pelo tamanho ou assume Brasil
    if (!countryCode) {
        // Se tiver 8-9 dígitos sem DDD, assume que é brasileiro e adiciona 55 + um DDD padrão (11)
        if (cleaned.length <= 9) {
            console.log(`Número curto detectado: ${cleaned}. Adicionando código do Brasil (55) e DDD padrão.`);
            cleaned = '5511' + cleaned;
        } 
        // Se tiver 10-11 dígitos (número brasileiro típico com DDD), adiciona só o 55
        else if (cleaned.length >= 10 && cleaned.length <= 11) {
            console.log(`Número sem código de país detectado: ${cleaned}. Adicionando código do Brasil (55).`);
            cleaned = '55' + cleaned;
        }
        // Se for maior, assume que já tem o código mas não foi reconhecido
        else {
            console.log(`Número longo não reconhecido: ${cleaned}. Mantendo original.`);
        }
    } else {
        console.log(`Código de país detectado: +${countryCode} (${countryCodes[countryCode].name})`);
    }
    
    return cleaned;
}

// Rota para analisar um número e retornar informações do país
app.post('/api/analyze-number', (req, res) => {
    const { number } = req.body;
    
    if (!number) {
        return res.status(400).json({ error: 'Número é obrigatório' });
    }
    
    try {
        // Remove todos os caracteres que não são dígitos
        let cleaned = number.replace(/\D/g, '');
        let countryInfo = { code: null, country: 'Desconhecido', isFormatted: false };
        
        // Verifica se o número já começa com um código de país conhecido
        for (const code in countryCodes) {
            if (cleaned.startsWith(code)) {
                countryInfo.code = code;
                countryInfo.country = countryCodes[code].name;
                countryInfo.isFormatted = true;
                break;
            }
        }
        
        // Retorna a informação do país
        res.json({
            original: number,
            cleaned: cleaned,
            countryInfo: countryInfo,
            formattedNumber: formatPhoneNumber(number)
        });
    } catch (error) {
        console.error('Erro ao analisar número:', error);
        res.status(500).json({ error: 'Erro ao analisar número', details: error.message });
    }
});

// Rota para analisar todos os números de um lote
app.post('/api/analyze-batch', (req, res) => {
    const { numbers } = req.body;
    
    if (!numbers || !Array.isArray(numbers)) {
        return res.status(400).json({ error: 'Lista de números é obrigatória' });
    }
    
    try {
        const results = numbers.map(number => {
            // Remove todos os caracteres que não são dígitos
            const cleaned = number.replace(/\D/g, '');
            let countryInfo = { code: null, country: 'Desconhecido', isFormatted: false };
            
            // Verifica se o número já começa com um código de país conhecido
            for (const code in countryCodes) {
                if (cleaned.startsWith(code)) {
                    countryInfo.code = code;
                    countryInfo.country = countryCodes[code].name;
                    countryInfo.isFormatted = true;
                    break;
                }
            }
            
            return {
                original: number,
                cleaned: cleaned,
                countryInfo: countryInfo,
                formattedNumber: formatPhoneNumber(number)
            };
        });
        
        // Estatísticas por país
        const countryStats = {};
        results.forEach(result => {
            const country = result.countryInfo.country;
            if (!countryStats[country]) {
                countryStats[country] = 0;
            }
            countryStats[country]++;
        });
        
        res.json({
            results: results,
            stats: {
                total: results.length,
                formatted: results.filter(r => r.countryInfo.isFormatted).length,
                byCountry: countryStats
            }
        });
    } catch (error) {
        console.error('Erro ao analisar lote de números:', error);
        res.status(500).json({ error: 'Erro ao analisar lote de números', details: error.message });
    }
});
// Rota para reiniciar a sessão do WhatsApp
app.post('/api/reset-session', async (req, res) => {
    try {
        console.log('Solicitação para reiniciar sessão do WhatsApp recebida');
        
        // Informa que vamos encerrar a sessão atual
        clientReady = false;
        
        // Tenta desconectar o cliente atual
        try {
            await client.destroy();
            console.log('Cliente destruído com sucesso');
        } catch (destroyError) {
            console.log('Erro ao destruir cliente:', destroyError);
            // Continuamos mesmo com erro, pois vamos recriar o cliente de qualquer forma
        }
        
        // Remove os arquivos de autenticação
        try {
            const authFolder = './whatsapp-session';
            if (fs.existsSync(authFolder)) {
                // Função para excluir pasta recursivamente
                const deleteFolderRecursive = function(path) {
                    if (fs.existsSync(path)) {
                        fs.readdirSync(path).forEach((file) => {
                            const curPath = path + "/" + file;
                            if (fs.lstatSync(curPath).isDirectory()) {
                                // Recursão para pastas
                                deleteFolderRecursive(curPath);
                            } else {
                                // Exclui arquivo
                                fs.unlinkSync(curPath);
                            }
                        });
                        fs.rmdirSync(path);
                    }
                };
                
                deleteFolderRecursive(authFolder);
                console.log('Pasta de autenticação removida com sucesso');
            }
        } catch (fsError) {
            console.log('Erro ao remover pasta de autenticação:', fsError);
            // Continuamos mesmo com erro
        }
        
        // Reinicia as variáveis globais
        clientReady = false;
        qrData = null;
        
        // Cria e inicializa um novo cliente
        client.initialize();
        console.log('Novo cliente inicializado, aguardando QR code');
        
        res.json({ success: true, message: 'Sessão reiniciada com sucesso' });
    } catch (error) {
        console.error('Erro ao reiniciar sessão:', error);
        res.status(500).json({ error: 'Falha ao reiniciar sessão', details: error.message });
    }
});
// Inicia o servidor
app.listen(port, () => {
    console.log(`Servidor rodando em http://localhost:${port}`);
});