// src/pages/AdminDashboard.js
import React, { useState, useEffect } from 'react';
import { 
  Container, Box, Grid, Typography, Paper, Tabs, Tab, Button,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  TablePagination, TextField, Dialog, DialogActions, DialogContent,
  DialogTitle, FormControl, InputLabel, Select, MenuItem, Chip,
  IconButton, Card, CardContent, CircularProgress, Alert
} from '@mui/material';
import { 
  Dashboard, People, Token, Message, Add, Edit, Delete, 
  Check, Block, Refresh, Add as AddIcon
} from '@mui/icons-material';
import { Bar, Line } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, LineElement, 
         PointElement, Title, Tooltip, Legend } from 'chart.js';
import { toast } from 'react-toastify';
import axios from 'axios';
import { API_URL } from '../config';
import { useAuth } from '../contexts/AuthContext';
import moment from 'moment';

// Register ChartJS components
ChartJS.register(
  CategoryScale, LinearScale, BarElement, LineElement, PointElement,
  Title, Tooltip, Legend
);

const AdminDashboard = () => {
  const { token } = useAuth();
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    totalUsers: 0,
    activeUsers: 0,
    totalTokensSold: 0,
    totalTokensUsed: 0,
    messagesSent: 0,
    activeConnections: 0
  });
  const [users, setUsers] = useState([]);
  const [tokenTransactions, setTokenTransactions] = useState([]);
  const [messages, setMessages] = useState([]);
  const [userDialogOpen, setUserDialogOpen] = useState(false);
  const [tokenDialogOpen, setTokenDialogOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [tokenAmount, setTokenAmount] = useState(0);
  const [tokenDescription, setTokenDescription] = useState('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [userFilter, setUserFilter] = useState('');
  const [chartData, setChartData] = useState({
    daily: {
      labels: [],
      datasets: []
    },
    tokenUsage: {
      labels: [],
      datasets: []
    }
  });
  
  // Load dashboard data
  useEffect(() => {
    const fetchDashboardData = async () => {
      setLoading(true);
      try {
        // Get dashboard statistics
        const statsRes = await axios.get(`${API_URL}/admin/stats`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setStats(statsRes.data);
        
        // Get users
        const usersRes = await axios.get(`${API_URL}/admin/users`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setUsers(usersRes.data);
        
        // Get token transactions
        const tokenRes = await axios.get(`${API_URL}/admin/tokens`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setTokenTransactions(tokenRes.data);
        
        // Get messages
        const messagesRes = await axios.get(`${API_URL}/admin/messages`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setMessages(messagesRes.data);
        
        // Get chart data
        const chartRes = await axios.get(`${API_URL}/admin/charts`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setChartData(chartRes.data);
        
        setLoading(false);
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
        toast.error('Erro ao carregar dados do painel');
        setLoading(false);
      }
    };
    
    fetchDashboardData();
  }, [token]);
  
  // Handle tab change
  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };
  
  // Handle user dialog open
  const handleOpenUserDialog = (user = null) => {
    setSelectedUser(user || {
      name: '',
      email: '',
      password: '',
      role: 'client',
      tokenBalance: 0,
      active: true
    });
    setUserDialogOpen(true);
  };
  
  // Handle token dialog open
  const handleOpenTokenDialog = (user) => {
    setSelectedUser(user);
    setTokenAmount(0);
    setTokenDescription('');
    setTokenDialogOpen(true);
  };
  
  // Add or edit user
  const handleSaveUser = async () => {
    try {
      if (selectedUser._id) {
        // Update existing user
        await axios.put(`${API_URL}/admin/users/${selectedUser._id}`, selectedUser, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('Usuário atualizado com sucesso');
      } else {
        // Create new user
        await axios.post(`${API_URL}/admin/users`, selectedUser, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('Usuário criado com sucesso');
      }
      
      // Refresh user list
      const usersRes = await axios.get(`${API_URL}/admin/users`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUsers(usersRes.data);
      
      setUserDialogOpen(false);
    } catch (error) {
      console.error('Error saving user:', error);
      toast.error(error.response?.data?.error || 'Erro ao salvar usuário');
    }
  };
  
  // Add tokens to user
  const handleAddTokens = async () => {
    try {
      await axios.post(`${API_URL}/admin/tokens/add`, {
        userId: selectedUser._id,
        amount: tokenAmount,
        description: tokenDescription || `Adição manual de ${tokenAmount} tokens`
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success(`${tokenAmount} tokens adicionados ao usuário ${selectedUser.name}`);
      
      // Refresh token transactions
      const tokenRes = await axios.get(`${API_URL}/admin/tokens`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTokenTransactions(tokenRes.data);
      
      // Refresh users to update token balance
      const usersRes = await axios.get(`${API_URL}/admin/users`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUsers(usersRes.data);
      
      setTokenDialogOpen(false);
    } catch (error) {
      console.error('Error adding tokens:', error);
      toast.error(error.response?.data?.error || 'Erro ao adicionar tokens');
    }
  };
  
  // Toggle user active status
  const toggleUserStatus = async (user) => {
    try {
      await axios.put(`${API_URL}/admin/users/${user._id}/toggle-status`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Update user in state
      const updatedUsers = users.map(u => 
        u._id === user._id ? { ...u, active: !u.active } : u
      );
      setUsers(updatedUsers);
      
      toast.success(`Usuário ${user.active ? 'desativado' : 'ativado'} com sucesso`);
    } catch (error) {
      console.error('Error toggling user status:', error);
      toast.error('Erro ao alterar status do usuário');
    }
  };
  
  // Refresh data
  const refreshData = async () => {
    setLoading(true);
    try {
      // Get dashboard statistics
      const statsRes = await axios.get(`${API_URL}/admin/stats`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStats(statsRes.data);
      
      // Get users
      const usersRes = await axios.get(`${API_URL}/admin/users`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUsers(usersRes.data);
      
      // Get token transactions
      const tokenRes = await axios.get(`${API_URL}/admin/tokens`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTokenTransactions(tokenRes.data);
      
      // Get messages
      const messagesRes = await axios.get(`${API_URL}/admin/messages`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMessages(messagesRes.data);
      
      // Get chart data
      const chartRes = await axios.get(`${API_URL}/admin/charts`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setChartData(chartRes.data);
      
      toast.success('Dados atualizados');
      setLoading(false);
    } catch (error) {
      console.error('Error refreshing data:', error);
      toast.error('Erro ao atualizar dados');
      setLoading(false);
    }
  };
  
  // Filter users by name or email
  const filteredUsers = users.filter(user => 
    user.name.toLowerCase().includes(userFilter.toLowerCase()) ||
    user.email.toLowerCase().includes(userFilter.toLowerCase())
  );
  
  // Handle page change
  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };
  
  // Handle rows per page change
  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  // Render dashboard overview
  const renderDashboardOverview = () => (
    <>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography component="h1" variant="h5">
          Visão Geral do Sistema
        </Typography>
        <Button 
          startIcon={<Refresh />} 
          onClick={refreshData}
          disabled={loading}
        >
          Atualizar
        </Button>
      </Box>
      
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 5 }}>
          <CircularProgress />
        </Box>
      ) : (
        <>
          {/* Stats Cards */}
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Usuários Ativos
                  </Typography>
                  <Typography variant="h4" component="div">
                    {stats.activeUsers}
                  </Typography>
                  <Typography color="textSecondary">
                    de {stats.totalUsers} total
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Tokens Vendidos
                  </Typography>
                  <Typography variant="h4" component="div">
                    {stats.totalTokensSold}
                  </Typography>
                  <Typography color="textSecondary">
                    {stats.totalTokensUsed} utilizados
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Mensagens Enviadas
                  </Typography>
                  <Typography variant="h4" component="div">
                    {stats.messagesSent}
                  </Typography>
                  <Typography color="textSecondary">
                    nos últimos 30 dias
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Conexões WhatsApp
                  </Typography>
                  <Typography variant="h4" component="div">
                    {stats.activeConnections}
                  </Typography>
                  <Typography color="textSecondary">
                    ativas no momento
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
          
          {/* Charts */}
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Mensagens Enviadas (Últimos 30 dias)
                </Typography>
                <Box sx={{ height: 300 }}>
                  <Bar 
                    data={chartData.daily}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: {
                          position: 'top',
                        },
                        title: {
                          display: false
                        }
                      }
                    }}
                  />
                </Box>
              </Paper>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Uso de Tokens (Últimos 30 dias)
                </Typography>
                <Box sx={{ height: 300 }}>
                  <Line 
                    data={chartData.tokenUsage}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: {
                          position: 'top',
                        },
                        title: {
                          display: false
                        }
                      }
                    }}
                  />
                </Box>
              </Paper>
            </Grid>
          </Grid>
          
          {/* Recent Activity */}
          <Grid container spacing={3} sx={{ mt: 2 }}>
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Transações Recentes
                </Typography>
                
                <TableContainer sx={{ maxHeight: 300 }}>
                  <Table stickyHeader size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Usuário</TableCell>
                        <TableCell>Tipo</TableCell>
                        <TableCell align="right">Quantidade</TableCell>
                        <TableCell>Data</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {tokenTransactions.slice(0, 5).map((transaction) => (
                        <TableRow key={transaction._id}>
                          <TableCell>{transaction.user.name}</TableCell>
                          <TableCell>
                            <Chip 
                              label={transaction.type} 
                              color={transaction.amount > 0 ? 'success' : 'error'}
                              size="small"
                            />
                          </TableCell>
                          <TableCell align="right">{transaction.amount}</TableCell>
                          <TableCell>{moment(transaction.createdAt).format('DD/MM/YYYY')}</TableCell>
                        </TableRow>
                      ))}
                      
                      {tokenTransactions.length === 0 && (
                        <TableRow>
                          <TableCell colSpan={4} align="center">Nenhuma transação encontrada</TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Paper>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Mensagens Recentes
                </Typography>
                
                <TableContainer sx={{ maxHeight: 300 }}>
                  <Table stickyHeader size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Usuário</TableCell>
                        <TableCell>Destinatários</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Data</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {messages.slice(0, 5).map((message) => (
                        <TableRow key={message._id}>
                          <TableCell>{message.user.name}</TableCell>
                          <TableCell>{message.recipientCount}</TableCell>
                          <TableCell>
                            <Chip 
                              label={message.status} 
                              color={
                                message.status === 'completed' ? 'success' :
                                message.status === 'processing' ? 'warning' :
                                message.status === 'queued' ? 'info' : 'error'
                              }
                              size="small"
                            />
                          </TableCell>
                          <TableCell>{moment(message.createdAt).format('DD/MM/YYYY')}</TableCell>
                        </TableRow>
                      ))}
                      
                      {messages.length === 0 && (
                        <TableRow>
                          <TableCell colSpan={4} align="center">Nenhuma mensagem encontrada</TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Paper>
            </Grid>
          </Grid>
        </>
      )}
    </>
  );
  
  // Render users management
  const renderUsersManagement = () => (
    <>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography component="h1" variant="h5">
          Gerenciamento de Usuários
        </Typography>
        <Button 
          variant="contained" 
          startIcon={<AddIcon />} 
          onClick={() => handleOpenUserDialog()}
        >
          Novo Usuário
        </Button>
      </Box>
      
      <Paper sx={{ p: 2, mb: 3 }}>
        <TextField
          label="Buscar por nome ou email"
          variant="outlined"
          size="small"
          fullWidth
          value={userFilter}
          onChange={(e) => setUserFilter(e.target.value)}
          sx={{ mb: 2 }}
        />
        
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Nome</TableCell>
                <TableCell>Email</TableCell>
                <TableCell>Função</TableCell>
                <TableCell align="right">Tokens</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Criado em</TableCell>
                <TableCell align="center">Ações</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    <CircularProgress size={30} />
                  </TableCell>
                </TableRow>
              ) : (
                <>
                  {filteredUsers
                    .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                    .map((user) => (
                      <TableRow key={user._id}>
                        <TableCell>{user.name}</TableCell>
                        <TableCell>{user.email}</TableCell>
                        <TableCell>
                          <Chip 
                            label={user.role === 'admin' ? 'Administrador' : 'Cliente'} 
                            color={user.role === 'admin' ? 'primary' : 'default'}
                            size="small"
                          />
                        </TableCell>
                        <TableCell align="right">{user.tokenBalance}</TableCell>
                        <TableCell>
                          <Chip 
                            label={user.active ? 'Ativo' : 'Inativo'} 
                            color={user.active ? 'success' : 'error'}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>{moment(user.createdAt).format('DD/MM/YYYY')}</TableCell>
                        <TableCell align="center">
                          <IconButton size="small" onClick={() => handleOpenUserDialog(user)}>
                            <Edit fontSize="small" />
                          </IconButton>
                          <IconButton size="small" onClick={() => handleOpenTokenDialog(user)}>
                            <Token fontSize="small" />
                          </IconButton>
                          <IconButton size="small" onClick={() => toggleUserStatus(user)}>
                            {user.active ? <Block fontSize="small" /> : <Check fontSize="small" />}
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                  
                  {filteredUsers.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={7} align="center">Nenhum usuário encontrado</TableCell>
                    </TableRow>
                  )}
                </>
              )}
            </TableBody>
          </Table>
        </TableContainer>
        
        <TablePagination
          rowsPerPageOptions={[10, 25, 50]}
          component="div"
          count={filteredUsers.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
          labelRowsPerPage="Linhas por página:"
          labelDisplayedRows={({ from, to, count }) => `${from}-${to} de ${count}`}
        />
      </Paper>
      
      {/* User Dialog */}
      <Dialog open={userDialogOpen} onClose={() => setUserDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{selectedUser?._id ? 'Editar Usuário' : 'Novo Usuário'}</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Nome"
            fullWidth
            value={selectedUser?.name || ''}
            onChange={(e) => setSelectedUser({ ...selectedUser, name: e.target.value })}
            sx={{ mb: 2 }}
          />
          
          <TextField
            margin="dense"
            label="Email"
            type="email"
            fullWidth
            value={selectedUser?.email || ''}
            onChange={(e) => setSelectedUser({ ...selectedUser, email: e.target.value })}
            sx={{ mb: 2 }}
          />
          
          {!selectedUser?._id && (
            <TextField
              margin="dense"
              label="Senha"
              type="password"
              fullWidth
              value={selectedUser?.password || ''}
              onChange={(e) => setSelectedUser({ ...selectedUser, password: e.target.value })}
              sx={{ mb: 2 }}
            />
          )}
          
          <FormControl fullWidth margin="dense" sx={{ mb: 2 }}>
            <InputLabel>Função</InputLabel>
            <Select
              value={selectedUser?.role || 'client'}
              onChange={(e) => setSelectedUser({ ...selectedUser, role: e.target.value })}
              label="Função"
            >
              <MenuItem value="client">Cliente</MenuItem>
              <MenuItem value="admin">Administrador</MenuItem>
            </Select>
          </FormControl>
          
          <FormControl fullWidth margin="dense" sx={{ mb: 2 }}>
            <InputLabel>Status</InputLabel>
            <Select
              value={selectedUser?.active}
              onChange={(e) => setSelectedUser({ ...selectedUser, active: e.target.value })}
              label="Status"
            >
              <MenuItem value={true}>Ativo</MenuItem>
              <MenuItem value={false}>Inativo</MenuItem>
            </Select>
          </FormControl>
          
          {selectedUser?._id && (
            <TextField
              margin="dense"
              label="Saldo de Tokens"
              type="number"
              fullWidth
              value={selectedUser?.tokenBalance || 0}
              onChange={(e) => setSelectedUser({ ...selectedUser, tokenBalance: parseInt(e.target.value) || 0 })}
              InputProps={{ readOnly: true }}
              helperText="Use a função 'Adicionar Tokens' para modificar o saldo"
            />
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUserDialogOpen(false)}>Cancelar</Button>
          <Button onClick={handleSaveUser} variant="contained">Salvar</Button>
        </DialogActions>
      </Dialog>
      
      {/* Token Dialog */}
      <Dialog open={tokenDialogOpen} onClose={() => setTokenDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Adicionar Tokens</DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 2 }}>
            Adicionando tokens para: <strong>{selectedUser?.name}</strong>
            <br />
            Saldo atual: <strong>{selectedUser?.tokenBalance} tokens</strong>
          </Alert>
          
          <TextField
            autoFocus
            margin="dense"
            label="Quantidade de Tokens"
            type="number"
            fullWidth
            value={tokenAmount}
            onChange={(e) => setTokenAmount(parseInt(e.target.value) || 0)}
            inputProps={{ min: 1 }}
            sx={{ mb: 2 }}
          />
          
          <TextField
            margin="dense"
            label="Descrição"
            fullWidth
            value={tokenDescription}
            onChange={(e) => setTokenDescription(e.target.value)}
            placeholder="Ex: Compra de pacote básico"
            helperText="Opcional - Uma descrição para esta transação"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTokenDialogOpen(false)}>Cancelar</Button>
          <Button 
            onClick={handleAddTokens} 
            variant="contained"
            disabled={tokenAmount <= 0}
          >
            Adicionar
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
  
  // Render token transactions
  const renderTokenTransactions = () => (
    <>
      <Typography component="h1" variant="h5" sx={{ mb: 3 }}>
        Histórico de Tokens
      </Typography>
      
      <Paper sx={{ p: 2 }}>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Usuário</TableCell>
                <TableCell>Tipo</TableCell>
                <TableCell align="right">Quantidade</TableCell>
                <TableCell align="right">Saldo Após</TableCell>
                <TableCell>Descrição</TableCell>
                <TableCell>Data</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={6} align="center">
                    <CircularProgress size={30} />
                  </TableCell>
                </TableRow>
              ) : (
                <>
                  {tokenTransactions
                    .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                    .map((transaction) => (
                      <TableRow key={transaction._id}>
                        <TableCell>{transaction.user.name}</TableCell>
                        <TableCell>
                          <Chip 
                            label={transaction.type} 
                            color={
                              transaction.type === 'purchase' || transaction.type === 'adjustment' ? 
                                (transaction.amount > 0 ? 'success' : 'error') :
                              transaction.type === 'consumption' ? 'warning' :
                              'default'
                            }
                            size="small"
                          />
                        </TableCell>
                        <TableCell align="right" 
                          sx={{ 
                            color: transaction.amount > 0 ? 'success.main' : 'error.main',
                            fontWeight: 'bold'
                          }}
                        >
                          {transaction.amount > 0 ? '+' : ''}{transaction.amount}
                        </TableCell>
                        <TableCell align="right">{transaction.balanceAfter}</TableCell>
                        <TableCell>{transaction.description}</TableCell>
                        <TableCell>{moment(transaction.createdAt).format('DD/MM/YYYY HH:mm')}</TableCell>
                      </TableRow>
                    ))}
                  
                  {tokenTransactions.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={6} align="center">Nenhuma transação encontrada</TableCell>
                    </TableRow>
                  )}
                </>
              )}
            </TableBody>
          </Table>
        </TableContainer>
        
        <TablePagination
          rowsPerPageOptions={[10, 25, 50]}
          component="div"
          count={tokenTransactions.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
          labelRowsPerPage="Linhas por página:"
          labelDisplayedRows={({ from, to, count }) => `${from}-${to} de ${count}`}
        />
      </Paper>
    </>
  );
  
  // Render message history
  const renderMessageHistory = () => (
    <>
      <Typography component="h1" variant="h5" sx={{ mb: 3 }}>
        Histórico de Mensagens
      </Typography>
      
      <Paper sx={{ p: 2 }}>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Usuário</TableCell>
                <TableCell>Tipo</TableCell>
                <TableCell align="right">Destinatários</TableCell>
                <TableCell align="right">Sucesso/Falha</TableCell>
                <TableCell align="right">Tokens</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Data</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    <CircularProgress size={30} />
                  </TableCell>
                </TableRow>
              ) : (
                <>
                  {messages
                    .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                    .map((message) => (
                      <TableRow key={message._id}>
                        <TableCell>{message.user.name}</TableCell>
                        <TableCell>
                          <Chip 
                            label={message.mediaType === 'none' ? 'Texto' : message.mediaType} 
                            color={message.mediaType === 'none' ? 'default' : 'primary'}
                            size="small"
                          />
                        </TableCell>
                        <TableCell align="right">{message.recipientCount}</TableCell>
                        <TableCell align="right">{message.successCount}/{message.failureCount}</TableCell>
                        <TableCell align="right">{message.tokensUsed}</TableCell>
                        <TableCell>
                          <Chip 
                            label={message.status} 
                            color={
                              message.status === 'completed' ? 'success' :
                              message.status === 'processing' ? 'warning' :
                              message.status === 'queued' ? 'info' : 'error'
                            }
                            size="small"
                          />
                        </TableCell>
                        <TableCell>{moment(message.createdAt).format('DD/MM/YYYY HH:mm')}</TableCell>
                      </TableRow>
                    ))}
                  
                  {messages.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={7} align="center">Nenhuma mensagem encontrada</TableCell>
                    </TableRow>
                  )}
                </>
              )}
            </TableBody>
          </Table>
        </TableContainer>
        
        <TablePagination
          rowsPerPageOptions={[10, 25, 50]}
          component="div"
          count={messages.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
          labelRowsPerPage="Linhas por página:"
          labelDisplayedRows={({ from, to, count }) => `${from}-${to} de ${count}`}
        />
      </Paper>
    </>
  );

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 8 }}>
      <Paper sx={{ p: 2, mb: 4 }}>
        <Tabs 
          value={activeTab} 
          onChange={handleTabChange}
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab icon={<Dashboard />} label="Dashboard" />
          <Tab icon={<People />} label="Usuários" />
          <Tab icon={<Token />} label="Tokens" />
          <Tab icon={<Message />} label="Mensagens" />
        </Tabs>
      </Paper>
      
      {activeTab === 0 && renderDashboardOverview()}
      {activeTab === 1 && renderUsersManagement()}
      {activeTab === 2 && renderTokenTransactions()}
      {activeTab === 3 && renderMessageHistory()}
    </Container>
  );
};

export default AdminDashboard;