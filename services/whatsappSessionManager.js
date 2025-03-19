// services/whatsappSessionManager.js
const { Client, LocalAuth, MessageMedia } = require('whatsapp-web.js');
const fs = require('fs');
const path = require('path');
const User = require('../models/User');
const WhatsAppSession = require('../models/WhatsAppSession');
const Message = require('../models/Message');
const TokenTransaction = require('../models/TokenTransaction');
const mongoose = require('mongoose');

class WhatsAppSessionManager {
  constructor(io) {
    this.io = io;
    this.clients = new Map(); // Map para armazenar instâncias de clientes ativos
    this.messageQueues = new Map(); // Map para armazenar filas de mensagens
    
    // Inicializar sessões existentes na inicialização do servidor
    this.initializeExistingSessions();
  }
  
  // Inicializa as sessões existentes do banco de dados
  async initializeExistingSessions() {
    try {
      const activeSessions = await WhatsAppSession.find({ 
        status: { $in: ['connecting', 'connected', 'authenticated'] } 
      }).populate('user');
      
      console.log(`Encontradas ${activeSessions.length} sessões ativas para inicializar`);
      
      for (const session of activeSessions) {
        try {
          // Só inicializa se o usuário estiver ativo
          if (session.user && session.user.active) {
            await this.initializeSession(session.user._id.toString());
          }
        } catch (error) {
          console.error(`Erro ao inicializar sessão para usuário ${session.user?._id}:`, error);
        }
      }
    } catch (error) {
      console.error('Erro ao inicializar sessões existentes:', error);
    }
  }
  
  // Inicializa uma nova sessão WhatsApp para o usuário
  async initializeSession(userId) {
    try {
      // Verifica se já existe um cliente para este usuário
      if (this.clients.has(userId)) {
        console.log(`Sessão já existe para o usuário ${userId}. Destruindo e recriando.`);
        await this.destroySession(userId);
      }
      
      console.log(`Inicializando nova sessão para o usuário ${userId}`);
      
      // Atualiza o status da sessão no banco de dados
      await WhatsAppSession.findOneAndUpdate(
        { user: userId },
        { 
          user: userId,
          status: 'connecting',
          lastActivity: new Date()
        },
        { upsert: true, new: true }
      );
      
      // Configura o diretório de sessão baseado no userId
      const sessionDir = path.join(__dirname, '..', 'whatsapp-sessions', userId);
      
      // Certifica-se de que o diretório de sessão existe
      if (!fs.existsSync(sessionDir)) {
        fs.mkdirSync(sessionDir, { recursive: true });
      }
      
      // Cria nova instância do cliente
      const client = new Client({
        authStrategy: new LocalAuth({
          dataPath: sessionDir
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
      
      // Configura os listeners de eventos
      this.setupClientEvents(client, userId);
      
      // Inicializa o cliente
      await client.initialize();
      
      // Armazena o cliente no mapa
      this.clients.set(userId, client);
      
      return true;
    } catch (error) {
      console.error(`Erro ao inicializar sessão para usuário ${userId}:`, error);
      
      // Atualiza o status da sessão para desconectado em caso de erro
      await WhatsAppSession.findOneAndUpdate(
        { user: userId },
        { status: 'disconnected', lastActivity: new Date() }
      );
      
      throw error;
    }
  }
  
  // Configura os eventos para um cliente WhatsApp
  setupClientEvents(client, userId) {
    // Evento de QR Code
    client.on('qr', async (qr) => {
      console.log(`QR Code recebido para usuário ${userId}`);
      
      // Salva o QR code no banco de dados
      await WhatsAppSession.findOneAndUpdate(
        { user: userId },
        { 
          qrCode: qr,
          status: 'connecting',
          lastActivity: new Date()
        }
      );
      
      // Envia o QR code para o cliente via socket.io
      this.io.to(`user-${userId}`).emit('whatsapp-qr', { qrCode: qr });
    });
    
    // Evento quando o cliente está pronto
    client.on('ready', async () => {
      console.log(`Cliente WhatsApp pronto para o usuário ${userId}`);
      
      // Atualiza o status no banco de dados
      await WhatsAppSession.findOneAndUpdate(
        { user: userId },
        { 
          status: 'authenticated',
          qrCode: null,
          lastActivity: new Date()
        }
      );
      
      // Envia notificação para o cliente via socket.io
      this.io.to(`user-${userId}`).emit('whatsapp-status', { 
        status: 'authenticated',
        message: 'WhatsApp conectado e pronto para enviar mensagens'
      });
      
      // Processa qualquer fila de mensagens pendente
      this.processMessageQueue(userId);
    });
    
    // Evento de autenticação
    client.on('authenticated', async () => {
      console.log(`Cliente WhatsApp autenticado para o usuário ${userId}`);
      
      // Atualiza o status no banco de dados
      await WhatsAppSession.findOneAndUpdate(
        { user: userId },
        { 
          status: 'connected',
          qrCode: null,
          lastActivity: new Date()
        }
      );
      
      // Envia notificação para o cliente via socket.io
      this.io.to(`user-${userId}`).emit('whatsapp-status', { 
        status: 'connected',
        message: 'WhatsApp autenticado, preparando conexão...'
      });
    });
    
    // Evento de desconexão
    client.on('disconnected', async (reason) => {
      console.log(`Cliente WhatsApp desconectado para o usuário ${userId}. Motivo: ${reason}`);
      
      // Atualiza o status no banco de dados
      await WhatsAppSession.findOneAndUpdate(
        { user: userId },
        { 
          status: 'disconnected',
          lastActivity: new Date()
        }
      );
      
      // Remove o cliente do mapa
      this.clients.delete(userId);
      
      // Envia notificação para o cliente via socket.io
      this.io.to(`user-${userId}`).emit('whatsapp-status', { 
        status: 'disconnected',
        message: 'WhatsApp desconectado. É necessário escanear o QR code novamente.'
      });
    });
    
    // Evento de falha na autenticação
    client.on('auth_failure', async (error) => {
      console.error(`Falha na autenticação para o usuário ${userId}:`, error);
      
      // Atualiza o status no banco de dados
      await WhatsAppSession.findOneAndUpdate(
        { user: userId },
        { 
          status: 'disconnected',
          lastActivity: new Date()
        }
      );
      
      // Envia notificação para o cliente via socket.io
      this.io.to(`user-${userId}`).emit('whatsapp-status', { 
        status: 'auth_failure',
        message: 'Falha na autenticação do WhatsApp. Tente novamente.'
      });
    });
  }
  
  // Obtém o status da sessão para um usuário
  async getSessionStatus(userId) {
    try {
      // Busca a sessão no banco de dados
      const session = await WhatsAppSession.findOne({ user: userId });
      
      if (!session) {
        return { 
          status: 'disconnected',
          message: 'Sessão não inicializada',
          qrCode: null
        };
      }
      
      return {
        status: session.status,
        message: this.getStatusMessage(session.status),
        qrCode: session.qrCode,
        lastActivity: session.lastActivity
      };
    } catch (error) {
      console.error(`Erro ao obter status da sessão para usuário ${userId}:`, error);
      throw error;
    }
  }
  
  // Obtém mensagem com base no status
  getStatusMessage(status) {
    switch (status) {
      case 'disconnected':
        return 'WhatsApp desconectado. Inicie a sessão e escaneie o QR code.';
      case 'connecting':
        return 'Conectando ao WhatsApp. Escaneie o QR code se solicitado.';
      case 'connected':
        return 'Conectado ao WhatsApp. Preparando sessão...';
      case 'authenticated':
        return 'WhatsApp conectado e pronto para enviar mensagens.';
      default:
        return 'Status desconhecido.';
    }
  }
  
  // Faz logout de uma sessão
  async logoutSession(userId) {
    try {
      const client = this.clients.get(userId);
      
      if (client) {
        console.log(`Desconectando sessão para o usuário ${userId}`);
        await this.destroySession(userId);
      }
      
      // Atualiza o status no banco de dados
      await WhatsAppSession.findOneAndUpdate(
        { user: userId },
        { 
          status: 'disconnected',
          qrCode: null,
          lastActivity: new Date()
        }
      );
      
      // Envia notificação para o cliente via socket.io
      this.io.to(`user-${userId}`).emit('whatsapp-status', { 
        status: 'disconnected',
        message: 'Sessão WhatsApp desconectada com sucesso.'
      });
      
      return true;
    } catch (error) {
      console.error(`Erro ao fazer logout da sessão para usuário ${userId}:`, error);
      throw error;
    }
  }
  
  // Destroi uma sessão e limpa os arquivos de sessão
  async destroySession(userId) {
    try {
      const client = this.clients.get(userId);
      
      if (client) {
        try {
          await client.destroy();
        } catch (destroyError) {
          console.error(`Erro ao destruir cliente para usuário ${userId}:`, destroyError);
        }
        
        this.clients.delete(userId);
      }
      
      return true;
    } catch (error) {
      console.error(`Erro ao destruir sessão para usuário ${userId}:`, error);
      throw error;
    }
  }
  
  // Enfileira mensagens para envio
  async queueMessages(userId, recipients, content, tokenCost) {
    const session = mongoose.startSession();
    session.startTransaction();
    
    try {
      // Cria um registro da mensagem
      const message = new Message({
        user: userId,
        content,
        mediaType: 'none',
        recipientCount: recipients.length,
        tokensUsed: tokenCost,
        status: 'queued'
      });
      
      await message.save({ session });
      
      // Debita os tokens do usuário
      const user = await User.findById(userId);
      
      if (user.tokenBalance < tokenCost) {
        throw new Error('Saldo de tokens insuficiente');
      }
      
      user.tokenBalance -= tokenCost;
      await user.save({ session });
      
      // Registra a transação de tokens
      await new TokenTransaction({
        user: userId,
        amount: -tokenCost,
        type: 'consumption',
        description: `Consumo de ${tokenCost} tokens para envio de ${recipients.length} mensagens`,
        balanceAfter: user.tokenBalance
      }).save({ session });
      
      // Cria ou adiciona à fila de mensagens
      if (!this.messageQueues.has(userId)) {
        this.messageQueues.set(userId, []);
      }
      
      this.messageQueues.get(userId).push({
        messageId: message._id,
        recipients,
        content,
        type: 'text'
      });
      
      // Processa a fila se o cliente estiver pronto
      const client = this.clients.get(userId);
      if (client && await this.isClientReady(userId)) {
        this.processMessageQueue(userId);
      }
      
      await session.commitTransaction();
      session.endSession();
      
      return message._id;
    } catch (error) {
      await session.abortTransaction();
      session.endSession();
      console.error(`Erro ao enfileirar mensagens para usuário ${userId}:`, error);
      throw error;
    }
  }
  
  // Enfileira mensagens com arquivo para envio
  async queueFileMessages(userId, recipients, filePath, caption, tokenCost) {
    const session = mongoose.startSession();
    session.startTransaction();
    
    try {
      // Determina o tipo de mídia com base na extensão do arquivo
      const fileExt = path.extname(filePath).toLowerCase();
      let mediaType = 'document';
      
      if (['.jpg', '.jpeg', '.png', '.gif'].includes(fileExt)) {
        mediaType = 'image';
      } else if (['.mp4', '.mkv', '.avi', '.mov'].includes(fileExt)) {
        mediaType = 'video';
      } else if (['.mp3', '.ogg', '.wav'].includes(fileExt)) {
        mediaType = 'audio';
      }
      
      // Cria um registro da mensagem
      const message = new Message({
        user: userId,
        content: caption,
        mediaType,
        mediaUrl: filePath,
        recipientCount: recipients.length,
        tokensUsed: tokenCost,
        status: 'queued'
      });
      
      await message.save({ session });
      
      // Debita os tokens do usuário
      const user = await User.findById(userId);
      
      if (user.tokenBalance < tokenCost) {
        throw new Error('Saldo de tokens insuficiente');
      }
      
      user.tokenBalance -= tokenCost;
      await user.save({ session });
      
      // Registra a transação de tokens
      await new TokenTransaction({
        user: userId,
        amount: -tokenCost,
        type: 'consumption',
        description: `Consumo de ${tokenCost} tokens para envio de ${recipients.length} mensagens com mídia`,
        balanceAfter: user.tokenBalance
      }).save({ session });
      
      // Cria ou adiciona à fila de mensagens
      if (!this.messageQueues.has(userId)) {
        this.messageQueues.set(userId, []);
      }
      
      this.messageQueues.get(userId).push({
        messageId: message._id,
        recipients,
        filePath,
        caption,
        type: 'media'
      });
      
      // Processa a fila se o cliente estiver pronto
      const client = this.clients.get(userId);
      if (client && await this.isClientReady(userId)) {
        this.processMessageQueue(userId);
      }
      
      await session.commitTransaction();
      session.endSession();
      
      return message._id;
    } catch (error) {
      await session.abortTransaction();
      session.endSession();
      console.error(`Erro ao enfileirar mensagens com arquivo para usuário ${userId}:`, error);
      throw error;
    }
  }
  
  // Verifica se o cliente está pronto para enviar mensagens
  async isClientReady(userId) {
    const session = await WhatsAppSession.findOne({ user: userId });
    return session && session.status === 'authenticated';
  }
  
  // Processa a fila de mensagens
  async processMessageQueue(userId) {
    if (!this.messageQueues.has(userId) || this.messageQueues.get(userId).length === 0) {
      return;
    }
    
    // Verifica se o cliente está pronto
    if (!await this.isClientReady(userId)) {
      console.log(`Cliente não está pronto para usuário ${userId}. Fila de mensagens em espera.`);
      return;
    }
    
    const client = this.clients.get(userId);
    if (!client) {
      console.log(`Cliente não encontrado para usuário ${userId}`);
      return;
    }
    
    console.log(`Processando fila de mensagens para usuário ${userId}`);
    
    // Obtém a próxima mensagem na fila
    const queue = this.messageQueues.get(userId);
    const messageTask = queue.shift();
    
    try {
      // Atualiza o status da mensagem
      await Message.findByIdAndUpdate(messageTask.messageId, {
        status: 'processing'
      });
      
      const successNumbers = [];
      const failureNumbers = [];
      const errorDetails = [];
      
      // Processa cada destinatário
      for (const number of messageTask.recipients) {
        try {
          // Formata o número para o padrão internacional
          const formattedNumber = this.formatPhoneNumber(number);
          
          // Envia texto ou mídia dependendo do tipo
          if (messageTask.type === 'text') {
            await client.sendMessage(`${formattedNumber}@c.us`, messageTask.content);
          } else if (messageTask.type === 'media') {
            const media = MessageMedia.fromFilePath(messageTask.filePath);
            await client.sendMessage(`${formattedNumber}@c.us`, media, {
              caption: messageTask.caption || ''
            });
          }
          
          // Adiciona à lista de sucesso
          successNumbers.push(number);
          
          // Pequeno atraso entre mensagens para evitar bloqueio
          await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 1000));
        } catch (error) {
          console.error(`Erro ao enviar mensagem para ${number}:`, error);
          failureNumbers.push(number);
          errorDetails.push({
            number,
            error: error.message
          });
        }
      }
      
      // Atualiza o registro da mensagem com os resultados
      await Message.findByIdAndUpdate(messageTask.messageId, {
        status: 'completed',
        successCount: successNumbers.length,
        failureCount: failureNumbers.length,
        errorDetails
      });
      
      // Remove o arquivo se foi uma mensagem com mídia
      if (messageTask.type === 'media' && fs.existsSync(messageTask.filePath)) {
        fs.unlinkSync(messageTask.filePath);
      }
      
      // Notifica o cliente sobre o progresso via socket.io
      this.io.to(`user-${userId}`).emit('message-status', {
        messageId: messageTask.messageId,
        status: 'completed',
        successCount: successNumbers.length,
        failureCount: failureNumbers.length
      });
      
      // Processa a próxima mensagem na fila se houver
      if (queue.length > 0) {
        this.processMessageQueue(userId);
      }
    } catch (error) {
      console.error(`Erro ao processar mensagem para usuário ${userId}:`, error);
      
      // Atualiza o registro da mensagem com erro
      await Message.findByIdAndUpdate(messageTask.messageId, {
        status: 'failed',
        errorDetails: [{ error: error.message }]
      });
      
      // Notifica o cliente sobre o erro via socket.io
      this.io.to(`user-${userId}`).emit('message-status', {
        messageId: messageTask.messageId,
        status: 'failed',
        error: error.message
      });
      
      // Continua processando a fila
      if (queue.length > 0) {
        this.processMessageQueue(userId);
      }
    }
  }
  
  // Formata número de telefone para padrão internacional
  formatPhoneNumber(number) {
    // Remove todos os caracteres que não são dígitos
    let cleaned = number.replace(/\D/g, '');
    
    // Lista de códigos de país comuns
    const countryCodes = {
      '1': 'EUA/Canadá',
      '44': 'Reino Unido',
      '351': 'Portugal',
      '55': 'Brasil',
      '61': 'Austrália',
      '81': 'Japão'
    };
    
    // Verifica se o número já começa com um código de país conhecido
    let hasCountryCode = false;
    for (const code in countryCodes) {
      if (cleaned.startsWith(code)) {
        hasCountryCode = true;
        break;
      }
    }
    
    // Se não tiver código de país, assume Brasil
    if (!hasCountryCode) {
      // Se tiver 8-9 dígitos sem DDD, adiciona DDD padrão (11)
      if (cleaned.length <= 9) {
        cleaned = '5511' + cleaned;
      } 
      // Se tiver 10-11 dígitos (número brasileiro com DDD), adiciona só o 55
      else if (cleaned.length >= 10 && cleaned.length <= 11) {
        cleaned = '55' + cleaned;
      }
    }
    
    return cleaned;
  }
}

module.exports = WhatsAppSessionManager;