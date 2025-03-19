// Modelo de Usuário (models/User.js)
const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');

const UserSchema = new mongoose.Schema({
  name: {
    type: String,
    required: true
  },
  email: {
    type: String,
    required: true,
    unique: true
  },
  password: {
    type: String,
    required: true
  },
  role: {
    type: String,
    enum: ['admin', 'client'],
    default: 'client'
  },
  tokenBalance: {
    type: Number,
    default: 0
  },
  active: {
    type: Boolean,
    default: true
  },
  createdAt: {
    type: Date,
    default: Date.now
  }
});

// Hash senha antes de salvar
UserSchema.pre('save', async function(next) {
  if (!this.isModified('password')) {
    return next();
  }
  
  try {
    const salt = await bcrypt.genSalt(10);
    this.password = await bcrypt.hash(this.password, salt);
    next();
  } catch (err) {
    next(err);
  }
});

// Método para comparar senha
UserSchema.methods.comparePassword = async function(candidatePassword) {
  return await bcrypt.compare(candidatePassword, this.password);
};

module.exports = mongoose.model('User', UserSchema);

// Modelo de Transação de Tokens (models/TokenTransaction.js)
const TokenTransactionSchema = new mongoose.Schema({
  user: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true
  },
  amount: {
    type: Number,
    required: true
  },
  type: {
    type: String,
    enum: ['purchase', 'consumption', 'refund', 'adjustment'],
    required: true
  },
  description: {
    type: String
  },
  balanceAfter: {
    type: Number,
    required: true
  },
  createdBy: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User'
  },
  createdAt: {
    type: Date,
    default: Date.now
  }
});

module.exports = mongoose.model('TokenTransaction', TokenTransactionSchema);

// Modelo de Sessão WhatsApp (models/WhatsAppSession.js)
const WhatsAppSessionSchema = new mongoose.Schema({
  user: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true,
    unique: true
  },
  status: {
    type: String,
    enum: ['disconnected', 'connecting', 'connected', 'authenticated'],
    default: 'disconnected'
  },
  qrCode: {
    type: String
  },
  lastActivity: {
    type: Date,
    default: Date.now
  },
  deviceInfo: {
    type: Object
  },
  createdAt: {
    type: Date,
    default: Date.now
  }
});

module.exports = mongoose.model('WhatsAppSession', WhatsAppSessionSchema);

// Modelo de Mensagem (models/Message.js)
const MessageSchema = new mongoose.Schema({
  user: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true
  },
  content: {
    type: String
  },
  mediaType: {
    type: String,
    enum: ['none', 'image', 'document', 'video', 'audio'],
    default: 'none'
  },
  mediaUrl: {
    type: String
  },
  recipientCount: {
    type: Number,
    required: true
  },
  successCount: {
    type: Number,
    default: 0
  },
  failureCount: {
    type: Number,
    default: 0
  },
  tokensUsed: {
    type: Number,
    required: true
  },
  status: {
    type: String,
    enum: ['queued', 'processing', 'completed', 'failed'],
    default: 'queued'
  },
  errorDetails: [{
    number: String,
    error: String
  }],
  createdAt: {
    type: Date,
    default: Date.now
  }
});

module.exports = mongoose.model('Message', MessageSchema);