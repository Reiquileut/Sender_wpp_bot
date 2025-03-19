// routes/tokens.js
const express = require('express');
const router = express.Router();
const mongoose = require('mongoose');
const User = require('../models/User');
const TokenTransaction = require('../models/TokenTransaction');
const { verifyToken, checkRole } = require('../middleware/auth');

// @route   GET /api/tokens/history
// @desc    Get token transaction history for current user
// @access  Private
router.get('/history', verifyToken, async (req, res) => {
  try {
    const transactions = await TokenTransaction.find({ user: req.user.id })
      .sort({ createdAt: -1 })
      .populate('user', 'name email');
    
    res.json(transactions);
  } catch (error) {
    console.error('Error getting token history:', error);
    res.status(500).json({ error: 'Erro ao obter histórico de tokens' });
  }
});

// ADMIN ROUTES

// @route   POST /api/tokens/add
// @desc    Add tokens to a user (admin only)
// @access  Private/Admin
router.post('/add', [verifyToken, checkRole('admin')], async (req, res) => {
  const session = await mongoose.startSession();
  session.startTransaction();
  
  try {
    const { userId, amount, description } = req.body;
    
    if (!userId || !amount || amount <= 0) {
      return res.status(400).json({ error: 'ID do usuário e quantidade de tokens são obrigatórios' });
    }
    
    // Find user
    const user = await User.findById(userId).session(session);
    
    if (!user) {
      return res.status(404).json({ error: 'Usuário não encontrado' });
    }
    
    // Update user token balance
    const previousBalance = user.tokenBalance;
    user.tokenBalance += amount;
    await user.save({ session });
    
    // Record transaction
    const transaction = new TokenTransaction({
      user: userId,
      amount,
      type: 'purchase',
      description: description || `Adição manual de ${amount} tokens`,
      balanceAfter: user.tokenBalance,
      createdBy: req.user.id
    });
    
    await transaction.save({ session });
    
    await session.commitTransaction();
    session.endSession();
    
    res.json({ 
      success: true, 
      previousBalance,
      newBalance: user.tokenBalance,
      transaction: transaction._id
    });
  } catch (error) {
    await session.abortTransaction();
    session.endSession();
    
    console.error('Error adding tokens:', error);
    res.status(500).json({ error: 'Erro ao adicionar tokens' });
  }
});

// @route   POST /api/tokens/adjust
// @desc    Adjust user token balance (admin only)
// @access  Private/Admin
router.post('/adjust', [verifyToken, checkRole('admin')], async (req, res) => {
  const session = await mongoose.startSession();
  session.startTransaction();
  
  try {
    const { userId, amount, description } = req.body;
    
    if (!userId || !amount) {
      return res.status(400).json({ error: 'ID do usuário e quantidade de tokens são obrigatórios' });
    }
    
    // Find user
    const user = await User.findById(userId).session(session);
    
    if (!user) {
      return res.status(404).json({ error: 'Usuário não encontrado' });
    }
    
    // Check if adjustment would result in negative balance
    if (user.tokenBalance + amount < 0) {
      return res.status(400).json({ error: 'O ajuste resultaria em saldo negativo' });
    }
    
    // Update user token balance
    const previousBalance = user.tokenBalance;
    user.tokenBalance += amount;
    await user.save({ session });
    
    // Record transaction
    const transaction = new TokenTransaction({
      user: userId,
      amount,
      type: 'adjustment',
      description: description || `Ajuste de ${amount} tokens`,
      balanceAfter: user.tokenBalance,
      createdBy: req.user.id
    });
    
    await transaction.save({ session });
    
    await session.commitTransaction();
    session.endSession();
    
    res.json({ 
      success: true, 
      previousBalance,
      newBalance: user.tokenBalance,
      transaction: transaction._id
    });
  } catch (error) {
    await session.abortTransaction();
    session.endSession();
    
    console.error('Error adjusting tokens:', error);
    res.status(500).json({ error: 'Erro ao ajustar tokens' });
  }
});

// @route   GET /api/tokens/packages
// @desc    Get available token packages
// @access  Private
router.get('/packages', verifyToken, async (req, res) => {
  try {
    // This could be stored in a database, but for simplicity we'll hardcode them
    const packages = [
      { id: 'basic', name: 'Básico', tokens: 100, price: 4900 },
      { id: 'standard', name: 'Padrão', tokens: 500, price: 19900 },
      { id: 'premium', name: 'Premium', tokens: 1000, price: 34900 },
      { id: 'enterprise', name: 'Empresarial', tokens: 5000, price: 149900 }
    ];
    
    res.json(packages);
  } catch (error) {
    console.error('Error getting token packages:', error);
    res.status(500).json({ error: 'Erro ao obter pacotes de tokens' });
  }
});

// @route   POST /api/tokens/purchase
// @desc    Process token purchase
// @access  Private
router.post('/purchase', verifyToken, async (req, res) => {
  const session = await mongoose.startSession();
  session.startTransaction();
  
  try {
    const { packageId, paymentMethod, paymentDetails } = req.body;
    
    // Get token package
    const packages = {
      'basic': { tokens: 100, price: 4900 },
      'standard': { tokens: 500, price: 19900 },
      'premium': { tokens: 1000, price: 34900 },
      'enterprise': { tokens: 5000, price: 149900 }
    };
    
    const selectedPackage = packages[packageId];
    
    if (!selectedPackage) {
      return res.status(400).json({ error: 'Pacote de tokens inválido' });
    }
    
    // Here you would integrate with a payment gateway
    // For now, we'll simulate a successful payment
    const paymentSuccessful = true;
    
    if (!paymentSuccessful) {
      return res.status(400).json({ error: 'Erro no processamento do pagamento' });
    }
    
    // Update user token balance
    const user = await User.findById(req.user.id).session(session);
    const previousBalance = user.tokenBalance;
    user.tokenBalance += selectedPackage.tokens;
    await user.save({ session });
    
    // Record transaction
    const transaction = new TokenTransaction({
      user: req.user.id,
      amount: selectedPackage.tokens,
      type: 'purchase',
      description: `Compra do pacote ${packageId} (${selectedPackage.tokens} tokens)`,
      balanceAfter: user.tokenBalance
    });
    
    await transaction.save({ session });
    
    await session.commitTransaction();
    session.endSession();
    
    res.json({
      success: true,
      packageId,
      tokensAdded: selectedPackage.tokens,
      newBalance: user.tokenBalance,
      transactionId: transaction._id
    });
  } catch (error) {
    await session.abortTransaction();
    session.endSession();
    
    console.error('Error purchasing tokens:', error);
    res.status(500).json({ error: 'Erro ao processar compra de tokens' });
  }
});

module.exports = router;