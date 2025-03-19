// routes/admin.js
const express = require('express');
const router = express.Router();
const mongoose = require('mongoose');
const User = require('../models/User');
const TokenTransaction = require('../models/TokenTransaction');
const Message = require('../models/Message');
const WhatsAppSession = require('../models/WhatsAppSession');
const { verifyToken, checkRole } = require('../middleware/auth');
const moment = require('moment');

// All routes in this file require admin role
router.use(verifyToken, checkRole('admin'));

// @route   GET /api/admin/stats
// @desc    Get dashboard statistics
// @access  Private/Admin
router.get('/stats', async (req, res) => {
  try {
    // Get user stats
    const totalUsers = await User.countDocuments();
    const activeUsers = await User.countDocuments({ active: true });
    
    // Get token stats
    const tokenStats = await TokenTransaction.aggregate([
      {
        $group: {
          _id: '$type',
          total: { $sum: '$amount' }
        }
      }
    ]);
    
    let totalTokensSold = 0;
    let totalTokensUsed = 0;
    
    tokenStats.forEach(stat => {
      if (stat._id === 'purchase' || (stat._id === 'adjustment' && stat.total > 0)) {
        totalTokensSold += stat.total;
      } else if (stat._id === 'consumption' || (stat._id === 'adjustment' && stat.total < 0)) {
        totalTokensUsed += Math.abs(stat.total);
      }
    });
    
    // Get message stats
    const thirtyDaysAgo = moment().subtract(30, 'days').toDate();
    const messagesSent = await Message.countDocuments({ 
      createdAt: { $gte: thirtyDaysAgo },
      status: 'completed'
    });
    
    // Get active WhatsApp connections
    const activeConnections = await WhatsAppSession.countDocuments({ 
      status: 'authenticated' 
    });
    
    res.json({
      totalUsers,
      activeUsers,
      totalTokensSold,
      totalTokensUsed,
      messagesSent,
      activeConnections
    });
  } catch (error) {
    console.error('Error getting admin stats:', error);
    res.status(500).json({ error: 'Erro ao obter estatísticas' });
  }
});

// @route   GET /api/admin/users
// @desc    Get all users
// @access  Private/Admin
router.get('/users', async (req, res) => {
  try {
    const users = await User.find().select('-password').sort({ createdAt: -1 });
    res.json(users);
  } catch (error) {
    console.error('Error getting users:', error);
    res.status(500).json({ error: 'Erro ao obter usuários' });
  }
});

// @route   POST /api/admin/users
// @desc    Create a new user
// @access  Private/Admin
router.post('/users', async (req, res) => {
  try {
    const { name, email, password, role, tokenBalance, active } = req.body;
    
    // Check if user already exists
    let user = await User.findOne({ email });
    if (user) {
      return res.status(400).json({ error: 'Usuário já existe com este email' });
    }
    
    // Create user
    user = new User({
      name,
      email,
      password,
      role: role || 'client',
      tokenBalance: tokenBalance || 0,
      active: active !== undefined ? active : true
    });
    
    await user.save();
    
    res.status(201).json({ 
      success: true,
      user: {
        id: user._id,
        name: user.name,
        email: user.email,
        role: user.role,
        tokenBalance: user.tokenBalance,
        active: user.active,
        createdAt: user.createdAt
      }
    });
  } catch (error) {
    console.error('Error creating user:', error);
    res.status(500).json({ error: 'Erro ao criar usuário' });
  }
});

// @route   PUT /api/admin/users/:id
// @desc    Update a user
// @access  Private/Admin
router.put('/users/:id', async (req, res) => {
  try {
    const { name, email, role, tokenBalance, active } = req.body;
    
    // Find user
    let user = await User.findById(req.params.id);
    if (!user) {
      return res.status(404).json({ error: 'Usuário não encontrado' });
    }
    
    // Update user fields
    if (name) user.name = name;
    if (email) user.email = email;
    if (role) user.role = role;
    if (tokenBalance !== undefined) user.tokenBalance = tokenBalance;
    if (active !== undefined) user.active = active;
    
    await user.save();
    
    res.json({ 
      success: true,
      user: {
        id: user._id,
        name: user.name,
        email: user.email,
        role: user.role,
        tokenBalance: user.tokenBalance,
        active: user.active,
        createdAt: user.createdAt
      }
    });
  } catch (error) {
    console.error('Error updating user:', error);
    res.status(500).json({ error: 'Erro ao atualizar usuário' });
  }
});

// @route   PUT /api/admin/users/:id/toggle-status
// @desc    Toggle user active status
// @access  Private/Admin
router.put('/users/:id/toggle-status', async (req, res) => {
  try {
    // Find user
    let user = await User.findById(req.params.id);
    if (!user) {
      return res.status(404).json({ error: 'Usuário não encontrado' });
    }
    
    // Toggle status
    user.active = !user.active;
    await user.save();
    
    res.json({ 
      success: true,
      userId: user._id,
      active: user.active
    });
  } catch (error) {
    console.error('Error toggling user status:', error);
    res.status(500).json({ error: 'Erro ao alterar status do usuário' });
  }
});

// @route   GET /api/admin/tokens
// @desc    Get all token transactions
// @access  Private/Admin
router.get('/tokens', async (req, res) => {
  try {
    const transactions = await TokenTransaction.find()
      .sort({ createdAt: -1 })
      .populate('user', 'name email')
      .populate('createdBy', 'name');
    
    res.json(transactions);
  } catch (error) {
    console.error('Error getting token transactions:', error);
    res.status(500).json({ error: 'Erro ao obter transações de tokens' });
  }
});

// @route   GET /api/admin/messages
// @desc    Get all messages
// @access  Private/Admin
router.get('/messages', async (req, res) => {
  try {
    const messages = await Message.find()
      .sort({ createdAt: -1 })
      .populate('user', 'name email');
    
    res.json(messages);
  } catch (error) {
    console.error('Error getting messages:', error);
    res.status(500).json({ error: 'Erro ao obter mensagens' });
  }
});

// @route   GET /api/admin/charts
// @desc    Get chart data
// @access  Private/Admin
router.get('/charts', async (req, res) => {
  try {
    // Get message stats by day (last 30 days)
    const thirtyDaysAgo = moment().subtract(30, 'days').startOf('day');
    
    // Prepare dates for last 30 days
    const dates = [];
    for (let i = 0; i < 30; i++) {
      dates.push(moment(thirtyDaysAgo).add(i, 'days').format('YYYY-MM-DD'));
    }
    
    // Get message counts by day
    const messagesByDay = await Message.aggregate([
      {
        $match: {
          createdAt: { $gte: thirtyDaysAgo.toDate() }
        }
      },
      {
        $group: {
          _id: {
            year: { $year: "$createdAt" },
            month: { $month: "$createdAt" },
            day: { $dayOfMonth: "$createdAt" }
          },
          count: { $sum: 1 },
          successCount: {
            $sum: "$successCount"
          },
          failureCount: {
            $sum: "$failureCount"
          }
        }
      },
      {
        $project: {
          _id: 0,
          date: {
            $dateToString: {
              format: "%Y-%m-%d",
              date: {
                $dateFromParts: {
                  year: "$_id.year",
                  month: "$_id.month",
                  day: "$_id.day"
                }
              }
            }
          },
          count: 1,
          successCount: 1,
          failureCount: 1
        }
      },
      {
        $sort: { date: 1 }
      }
    ]);
    
    // Fill in missing dates
    const filledMessagesByDay = dates.map(date => {
      const dayData = messagesByDay.find(d => d.date === date);
      return {
        date,
        count: dayData ? dayData.count : 0,
        successCount: dayData ? dayData.successCount : 0,
        failureCount: dayData ? dayData.failureCount : 0
      };
    });
    
    // Get token consumption by day
    const tokensByDay = await TokenTransaction.aggregate([
      {
        $match: {
          createdAt: { $gte: thirtyDaysAgo.toDate() }
        }
      },
      {
        $group: {
          _id: {
            year: { $year: "$createdAt" },
            month: { $month: "$createdAt" },
            day: { $dayOfMonth: "$createdAt" },
            type: "$type"
          },
          amount: { $sum: "$amount" }
        }
      },
      {
        $project: {
          _id: 0,
          date: {
            $dateToString: {
              format: "%Y-%m-%d",
              date: {
                $dateFromParts: {
                  year: "$_id.year",
                  month: "$_id.month",
                  day: "$_id.day"
                }
              }
            }
          },
          type: "$_id.type",
          amount: 1
        }
      },
      {
        $sort: { date: 1 }
      }
    ]);
    
    // Prepare token data by type and date
    const tokenDataByDate = {};
    
    // Initialize with all dates
    dates.forEach(date => {
      tokenDataByDate[date] = {
        purchase: 0,
        consumption: 0,
        refund: 0,
        adjustment: 0
      };
    });
    
    // Fill in actual data
    tokensByDay.forEach(data => {
      if (tokenDataByDate[data.date]) {
        // If it's consumption or negative adjustment, use absolute value
        const amount = data.type === 'consumption' || 
                      (data.type === 'adjustment' && data.amount < 0) 
                      ? Math.abs(data.amount) : data.amount;
        
        tokenDataByDate[data.date][data.type] = amount;
      }
    });
    
    // Format data for charts
    const dailyData = {
      labels: dates.map(date => moment(date).format('DD/MM')),
      datasets: [
        {
          label: 'Mensagens Enviadas',
          data: filledMessagesByDay.map(d => d.successCount),
          backgroundColor: 'rgba(54, 162, 235, 0.5)',
          borderColor: 'rgba(54, 162, 235, 1)',
          borderWidth: 1
        },
        {
          label: 'Falhas no Envio',
          data: filledMessagesByDay.map(d => d.failureCount),
          backgroundColor: 'rgba(255, 99, 132, 0.5)',
          borderColor: 'rgba(255, 99, 132, 1)',
          borderWidth: 1
        }
      ]
    };
    
    const tokenUsageData = {
      labels: dates.map(date => moment(date).format('DD/MM')),
      datasets: [
        {
          label: 'Tokens Comprados',
          data: dates.map(date => tokenDataByDate[date].purchase + 
                                  (tokenDataByDate[date].adjustment > 0 ? tokenDataByDate[date].adjustment : 0)),
          borderColor: 'rgba(75, 192, 192, 1)',
          backgroundColor: 'rgba(75, 192, 192, 0.2)',
          tension: 0.4
        },
        {
          label: 'Tokens Consumidos',
          data: dates.map(date => tokenDataByDate[date].consumption +
                                  (tokenDataByDate[date].adjustment < 0 ? tokenDataByDate[date].adjustment : 0)),
          borderColor: 'rgba(255, 159, 64, 1)',
          backgroundColor: 'rgba(255, 159, 64, 0.2)',
          tension: 0.4
        }
      ]
    };
    
    res.json({
      daily: dailyData,
      tokenUsage: tokenUsageData
    });
  } catch (error) {
    console.error('Error getting chart data:', error);
    res.status(500).json({ error: 'Erro ao obter dados dos gráficos' });
  }
});

module.exports = router;