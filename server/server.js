// server.js - Servidor WhatsApp com sistema de tokens.
require('dotenv').config();
const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const http = require('http');
const socketIo = require('socket.io');
const { Client, LocalAuth, MessageMedia } = require('whatsapp-web.js');
const multer = require('multer');
const path = require('path');
const authRoutes = require('./routes/auth');
const userRoutes = require('./routes/users');
const tokenRoutes = require('./routes/tokens');
const messageRoutes = require('./routes/messages');
const { verifyToken } = require('./middleware/auth');
const WhatsAppSessionManager = require('./services/whatsappSessionManager');

// Inicialização do Express
const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
  cors: {
    origin: process.env.FRONTEND_URL || "*",
    methods: ["GET", "POST"]
  }
});

// Middlewares
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Configuração do multer para upload de arquivos
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, 'uploads/');
  },
  filename: (req, file, cb) => {
    cb(null, Date.now() + '-' + file.originalname);
  }
});
const upload = multer({ storage });

// Conexão com MongoDB
mongoose.connect(process.env.MONGODB_URI, {
  useNewUrlParser: true,
  useUnifiedTopology: true,
})
.then(() => console.log('MongoDB conectado'))
.catch(err => console.error('Erro na conexão com MongoDB:', err));

// Inicialização do gerenciador de sessões WhatsApp
const sessionManager = new WhatsAppSessionManager(io);

// Rotas de autenticação (não precisam de token)
app.use('/api/auth', authRoutes);

// Middleware para verificar token em rotas protegidas
app.use('/api/users', verifyToken, userRoutes);
app.use('/api/tokens', verifyToken, tokenRoutes);
app.use('/api/messages', verifyToken, messageRoutes);

// Rotas para WhatsApp
app.get('/api/whatsapp/status/:userId', verifyToken, async (req, res) => {
  try {
    const { userId } = req.params;
    
    // Verifica se o usuário tem permissão para acessar essa sessão
    if (req.user.role !== 'admin' && req.user.id !== userId) {
      return res.status(403).json({ error: 'Acesso negado' });
    }
    
    const sessionStatus = await sessionManager.getSessionStatus(userId);
    res.json(sessionStatus);
  } catch (error) {
    console.error('Erro ao obter status do WhatsApp:', error);
    res.status(500).json({ error: 'Erro ao obter status do WhatsApp' });
  }
});

app.post('/api/whatsapp/init/:userId', verifyToken, async (req, res) => {
  try {
    const { userId } = req.params;
    
    // Verifica se o usuário tem permissão para inicializar essa sessão
    if (req.user.role !== 'admin' && req.user.id !== userId) {
      return res.status(403).json({ error: 'Acesso negado' });
    }
    
    await sessionManager.initializeSession(userId);
    res.json({ success: true, message: 'Sessão inicializada' });
  } catch (error) {
    console.error('Erro ao inicializar sessão:', error);
    res.status(500).json({ error: 'Erro ao inicializar sessão do WhatsApp' });
  }
});

app.post('/api/whatsapp/logout/:userId', verifyToken, async (req, res) => {
  try {
    const { userId } = req.params;
    
    // Verifica se o usuário tem permissão para desconectar essa sessão
    if (req.user.role !== 'admin' && req.user.id !== userId) {
      return res.status(403).json({ error: 'Acesso negado' });
    }
    
    await sessionManager.logoutSession(userId);
    res.json({ success: true, message: 'Sessão desconectada' });
  } catch (error) {
    console.error('Erro ao desconectar sessão:', error);
    res.status(500).json({ error: 'Erro ao desconectar sessão do WhatsApp' });
  }
});

app.post('/api/whatsapp/send-message', verifyToken, async (req, res) => {
  try {
    const { recipients, message, tokenCost = 1 } = req.body;
    const userId = req.user.id;
    
    // Verifica se o usuário tem tokens suficientes
    const User = require('./models/User');
    const user = await User.findById(userId);
    
    if (!user) {
      return res.status(404).json({ error: 'Usuário não encontrado' });
    }
    
    const totalCost = recipients.length * tokenCost;
    
    if (user.tokenBalance < totalCost) {
      return res.status(400).json({ 
        error: 'Saldo de tokens insuficiente',
        required: totalCost,
        available: user.tokenBalance
      });
    }
    
    // Verifica se a sessão está ativa
    const sessionStatus = await sessionManager.getSessionStatus(userId);
    if (sessionStatus.status !== 'authenticated') {
      return res.status(400).json({ 
        error: 'Sessão WhatsApp não está autenticada',
        status: sessionStatus.status
      });
    }
    
    // Inicia o envio de mensagens
    const messageId = await sessionManager.queueMessages(userId, recipients, message, totalCost);
    
    res.json({
      success: true,
      message: 'Mensagens enfileiradas para envio',
      messageId,
      tokenCost: totalCost
    });
  } catch (error) {
    console.error('Erro ao enviar mensagem:', error);
    res.status(500).json({ error: 'Erro ao enviar mensagem' });
  }
});

app.post('/api/whatsapp/send-file', verifyToken, upload.single('file'), async (req, res) => {
  try {
    const { recipients } = req.body;
    const caption = req.body.caption || '';
    const userId = req.user.id;
    const tokenCost = 2; // Custo maior para mensagens com mídia
    
    if (!req.file) {
      return res.status(400).json({ error: 'Nenhum arquivo enviado' });
    }
    
    // Verifica se o usuário tem tokens suficientes
    const User = require('./models/User');
    const user = await User.findById(userId);
    
    if (!user) {
      return res.status(404).json({ error: 'Usuário não encontrado' });
    }
    
    const totalCost = recipients.length * tokenCost;
    
    if (user.tokenBalance < totalCost) {
      return res.status(400).json({ 
        error: 'Saldo de tokens insuficiente',
        required: totalCost,
        available: user.tokenBalance
      });
    }
    
    // Verifica se a sessão está ativa
    const sessionStatus = await sessionManager.getSessionStatus(userId);
    if (sessionStatus.status !== 'authenticated') {
      return res.status(400).json({ 
        error: 'Sessão WhatsApp não está autenticada',
        status: sessionStatus.status
      });
    }
    
    // Prepara o arquivo e enfileira para envio
    const messageId = await sessionManager.queueFileMessages(
      userId, 
      recipients, 
      req.file.path, 
      caption, 
      totalCost
    );
    
    res.json({
      success: true,
      message: 'Arquivo enfileirado para envio',
      messageId,
      tokenCost: totalCost
    });
  } catch (error) {
    console.error('Erro ao enviar arquivo:', error);
    res.status(500).json({ error: 'Erro ao enviar arquivo' });
  }
});

// Conexão de Socket.io para atualizações em tempo real
io.on('connection', (socket) => {
  console.log('Novo cliente conectado:', socket.id);
  
  socket.on('join-user-room', (userId) => {
    console.log(`Usuário ${userId} entrou na sala`);
    socket.join(`user-${userId}`);
  });
  
  socket.on('disconnect', () => {
    console.log('Cliente desconectado:', socket.id);
  });
});

// Rota para o frontend (React)
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Iniciar o servidor
const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
  console.log(`Servidor rodando na porta ${PORT}`);
});