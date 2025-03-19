// routes/auth.js
const express = require('express');
const router = express.Router();
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const crypto = require('crypto');
const User = require('../models/User');
const { verifyToken } = require('../middleware/auth');
const sendEmail = require('../services/emailService');

// @route   POST /api/auth/register
// @desc    Register a new user
// @access  Public
router.post('/register', async (req, res) => {
  try {
    const { name, email, password } = req.body;
    
    // Check if user already exists
    let user = await User.findOne({ email });
    if (user) {
      return res.status(400).json({ message: 'Usuário já existe com este email' });
    }
    
    // Create new user
    user = new User({
      name,
      email,
      password,
      role: 'client', // Default role
      tokenBalance: 0
    });
    
    await user.save();
    
    res.status(201).json({ message: 'Usuário registrado com sucesso' });
  } catch (error) {
    console.error('Registration error:', error);
    res.status(500).json({ message: 'Erro no servidor' });
  }
});

// @route   POST /api/auth/login
// @desc    Authenticate user & get token
// @access  Public
router.post('/login', async (req, res) => {
  try {
    const { email, password } = req.body;
    
    // Check for user
    const user = await User.findOne({ email });
    if (!user) {
      return res.status(400).json({ message: 'Credenciais inválidas' });
    }
    
    // Check if user is active
    if (!user.active) {
      return res.status(401).json({ message: 'Conta desativada. Entre em contato com o suporte.' });
    }
    
    // Check password
    const isMatch = await user.comparePassword(password);
    if (!isMatch) {
      return res.status(400).json({ message: 'Credenciais inválidas' });
    }
    
    // Create token
    const payload = {
      user: {
        id: user.id,
        role: user.role
      }
    };
    
    jwt.sign(
      payload,
      process.env.JWT_SECRET,
      { expiresIn: '24h' },
      (err, token) => {
        if (err) throw err;
        
        // Return user data (without password) and token
        const userData = {
          id: user._id,
          name: user.name,
          email: user.email,
          role: user.role,
          tokenBalance: user.tokenBalance,
          createdAt: user.createdAt
        };
        
        res.json({ token, user: userData });
      }
    );
  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({ message: 'Erro no servidor' });
  }
});

// @route   GET /api/auth/me
// @desc    Get current user
// @access  Private
router.get('/me', verifyToken, async (req, res) => {
  try {
    const user = await User.findById(req.user.id).select('-password');
    
    if (!user) {
      return res.status(404).json({ message: 'Usuário não encontrado' });
    }
    
    res.json(user);
  } catch (error) {
    console.error('Get user error:', error);
    res.status(500).json({ message: 'Erro no servidor' });
  }
});

// @route   POST /api/auth/forgot-password
// @desc    Send password reset email
// @access  Public
router.post('/forgot-password', async (req, res) => {
  try {
    const { email } = req.body;
    
    // Find user
    const user = await User.findOne({ email });
    if (!user) {
      return res.status(404).json({ message: 'Usuário não encontrado' });
    }
    
    // Generate reset token
    const resetToken = crypto.randomBytes(20).toString('hex');
    const resetTokenExpiration = Date.now() + 3600000; // 1 hour
    
    // Save token to user
    user.resetPasswordToken = resetToken;
    user.resetPasswordExpires = resetTokenExpiration;
    await user.save();
    
    // Send email
    const resetUrl = `${process.env.FRONTEND_URL}/reset-password/${resetToken}`;
    
    const emailData = {
      to: user.email,
      subject: 'Recuperação de Senha - WhatsApp Messenger',
      text: `Você solicitou a recuperação de senha. Por favor, clique no link a seguir para definir uma nova senha: ${resetUrl}`,
      html: `
        <h1>Recuperação de Senha</h1>
        <p>Você solicitou a recuperação de senha para sua conta no WhatsApp Messenger.</p>
        <p>Por favor, clique no botão abaixo para definir uma nova senha:</p>
        <a href="${resetUrl}" style="display:inline-block;padding:10px 20px;background-color:#4CAF50;color:#fff;text-decoration:none;border-radius:4px;">
          Redefinir Senha
        </a>
        <p>Se você não solicitou a recuperação de senha, ignore este email.</p>
        <p>Este link expira em 1 hora.</p>
      `
    };
    
    await sendEmail(emailData);
    
    res.json({ message: 'Email de recuperação enviado' });
  } catch (error) {
    console.error('Forgot password error:', error);
    res.status(500).json({ message: 'Erro ao enviar email de recuperação' });
  }
});

// @route   POST /api/auth/reset-password
// @desc    Reset password
// @access  Public
router.post('/reset-password', async (req, res) => {
  try {
    const { token, password } = req.body;
    
    // Find user with token
    const user = await User.findOne({
      resetPasswordToken: token,
      resetPasswordExpires: { $gt: Date.now() }
    });
    
    if (!user) {
      return res.status(400).json({ message: 'Token inválido ou expirado' });
    }
    
    // Set new password
    user.password = password;
    user.resetPasswordToken = undefined;
    user.resetPasswordExpires = undefined;
    
    await user.save();
    
    res.json({ message: 'Senha alterada com sucesso' });
  } catch (error) {
    console.error('Reset password error:', error);
    res.status(500).json({ message: 'Erro ao redefinir senha' });
  }
});

module.exports = router;