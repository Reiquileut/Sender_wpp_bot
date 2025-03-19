// src/pages/ClientDashboard.js
import React, { useState, useEffect, useRef } from 'react';
import { Container, Box, Grid, Typography, Button, Paper, TextField, 
         FormControl, InputLabel, Select, MenuItem, Chip, Divider,
         CircularProgress, Alert, IconButton, Card, CardContent } from '@mui/material';
import { CloudUpload, Send, Refresh, WhatsApp, AccountBalance, Close } from '@mui/icons-material';
import QRCode from 'qrcode.react';
import { useDropzone } from 'react-dropzone';
import { toast } from 'react-toastify';
import axios from 'axios';
import { API_URL } from '../config';
import { useAuth } from '../contexts/AuthContext';
import io from 'socket.io-client';
import ContactListUploader from '../components/ContactListUploader';
import TokenHistory from '../components/TokenHistory';

const ClientDashboard = () => {
  const { user, token } = useAuth();
  const [whatsappStatus, setWhatsappStatus] = useState('loading');
  const [qrCode, setQrCode] = useState(null);
  const [message, setMessage] = useState('');
  const [contacts, setContacts] = useState([]);
  const [files, setFiles] = useState([]);
  const [selectedContacts, setSelectedContacts] = useState([]);
  const [isSending, setIsSending] = useState(false);
  const [tokenBalance, setTokenBalance] = useState(0);
  const [statusMessage, setStatusMessage] = useState('');
  const socketRef = useRef(null);
  
  // Connect to websocket
  useEffect(() => {
    // Load user data including token balance
    const fetchUserData = async () => {
      try {
        const res = await axios.get(`${API_URL}/users/me`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setTokenBalance(res.data.tokenBalance);
      } catch (error) {
        toast.error('Erro ao carregar dados do usuário');
        console.error(error);
      }
    };
    
    fetchUserData();
    
    // Check WhatsApp connection status
    checkWhatsAppStatus();
    
    // Setup socket connection
    socketRef.current = io(API_URL);
    
    socketRef.current.on('connect', () => {
      console.log('Connected to socket server');
      socketRef.current.emit('join-user-room', user.id);
    });
    
    socketRef.current.on('whatsapp-qr', (data) => {
      console.log('QR code received');
      setQrCode(data.qrCode);
    });
    
    socketRef.current.on('whatsapp-status', (data) => {
      console.log('WhatsApp status update:', data);
      setWhatsappStatus(data.status);
      setStatusMessage(data.message);
      if (data.status === 'authenticated') {
        setQrCode(null);
      }
    });
    
    socketRef.current.on('message-status', (data) => {
      console.log('Message status update:', data);
      
      if (data.status === 'completed') {
        toast.success(`Mensagem enviada com sucesso: ${data.successCount} de ${data.successCount + data.failureCount}`);
      } else if (data.status === 'failed') {
        toast.error(`Falha no envio da mensagem: ${data.error}`);
      }
      
      setIsSending(false);
      fetchUserData(); // Refresh token balance
    });
    
    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
      }
    };
  }, [user.id, token]);
  
  // Check WhatsApp connection status
  const checkWhatsAppStatus = async () => {
    try {
      const res = await axios.get(`${API_URL}/whatsapp/status/${user.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setWhatsappStatus(res.data.status);
      setStatusMessage(res.data.message);
      
      if (res.data.qrCode) {
        setQrCode(res.data.qrCode);
      }
    } catch (error) {
      console.error('Error checking WhatsApp status:', error);
      setWhatsappStatus('error');
      setStatusMessage('Erro ao verificar status do WhatsApp');
    }
  };
  
  // Initialize WhatsApp session
  const initializeWhatsApp = async () => {
    try {
      setWhatsappStatus('loading');
      setStatusMessage('Inicializando sessão...');
      
      await axios.post(`${API_URL}/whatsapp/init/${user.id}`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.info('Sessão WhatsApp inicializada. Aguardando QR Code...');
    } catch (error) {
      console.error('Error initializing WhatsApp session:', error);
      toast.error('Erro ao inicializar sessão WhatsApp');
      setWhatsappStatus('error');
      setStatusMessage('Erro ao inicializar sessão');
    }
  };
  
  // Logout WhatsApp session
  const logoutWhatsApp = async () => {
    try {
      setWhatsappStatus('loading');
      setStatusMessage('Desconectando sessão...');
      
      await axios.post(`${API_URL}/whatsapp/logout/${user.id}`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setQrCode(null);
      toast.info('Sessão WhatsApp desconectada');
    } catch (error) {
      console.error('Error logging out WhatsApp session:', error);
      toast.error('Erro ao desconectar sessão WhatsApp');
    }
  };
  
  // File upload handling
  const { getRootProps, getInputProps } = useDropzone({
    accept: {
      'image/*': ['.jpeg', '.png', '.jpg', '.gif'],
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'audio/*': ['.mp3', '.wav', '.ogg'],
      'video/*': ['.mp4', '.mov', '.avi']
    },
    maxFiles: 1,
    onDrop: acceptedFiles => {
      setFiles(acceptedFiles.map(file => Object.assign(file, {
        preview: URL.createObjectURL(file)
      })));
    }
  });
  
  // Remove uploaded file
  const removeFile = () => {
    setFiles([]);
  };
  
  // Handle sending messages
  const handleSendMessage = async () => {
    if (selectedContacts.length === 0) {
      toast.warning('Selecione pelo menos um contato');
      return;
    }
    
    if (!message && files.length === 0) {
      toast.warning('Digite uma mensagem ou anexe um arquivo');
      return;
    }
    
    // Check token balance
    const requiredTokens = selectedContacts.length * (files.length > 0 ? 2 : 1);
    if (tokenBalance < requiredTokens) {
      toast.error(`Saldo de tokens insuficiente. Necessários: ${requiredTokens}`);
      return;
    }
    
    setIsSending(true);
    
    try {
      if (files.length > 0) {
        // Send file message
        const formData = new FormData();
        formData.append('file', files[0]);
        formData.append('caption', message);
        
        selectedContacts.forEach(contact => {
          formData.append('recipients[]', contact);
        });
        
        await axios.post(`${API_URL}/whatsapp/send-file`, formData, {
          headers: { 
            Authorization: `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          }
        });
        
        toast.info(`Enviando arquivo para ${selectedContacts.length} contatos...`);
      } else {
        // Send text message
        await axios.post(`${API_URL}/whatsapp/send-message`, {
          recipients: selectedContacts,
          message
        }, {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        toast.info(`Enviando mensagem para ${selectedContacts.length} contatos...`);
      }
      
      // Clear form after sending
      setMessage('');
      setFiles([]);
    } catch (error) {
      console.error('Error sending message:', error);
      toast.error(error.response?.data?.error || 'Erro ao enviar mensagem');
      setIsSending(false);
    }
  };
  
  // Handler to select all contacts
  const handleSelectAllContacts = () => {
    setSelectedContacts(contacts.map(c => c.number));
  };
  
  // Handler to clear selected contacts
  const handleClearSelectedContacts = () => {
    setSelectedContacts([]);
  };
  
  // Render status badge
  const renderStatusBadge = () => {
    const statusColors = {
      loading: 'info',
      disconnected: 'error',
      connecting: 'warning',
      connected: 'info',
      authenticated: 'success',
      error: 'error'
    };
    
    return (
      <Alert 
        severity={statusColors[whatsappStatus] || 'info'}
        action={
          whatsappStatus === 'disconnected' ? (
            <Button color="inherit" size="small" onClick={initializeWhatsApp}>
              Conectar
            </Button>
          ) : whatsappStatus === 'authenticated' ? (
            <Button color="inherit" size="small" onClick={logoutWhatsApp}>
              Desconectar
            </Button>
          ) : null
        }
      >
        {statusMessage || 'Status desconhecido'}
      </Alert>
    );
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 8 }}>
      <Grid container spacing={3}>
        {/* WhatsApp Connection Status */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3, display: 'flex', flexDirection: 'column' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <WhatsApp color="primary" sx={{ mr: 1 }} />
              <Typography component="h2" variant="h6" color="primary">
                Status da Conexão WhatsApp
              </Typography>
            </Box>
            
            {renderStatusBadge()}
            
            {whatsappStatus === 'connecting' && qrCode && (
              <Box sx={{ mt: 2, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <Typography variant="subtitle1" gutterBottom>
                  Escaneie o QR Code com seu WhatsApp
                </Typography>
                <Paper elevation={3} sx={{ p: 2, bgcolor: 'white' }}>
                  <QRCode value={qrCode} size={256} level="H" />
                </Paper>
                <Typography variant="caption" sx={{ mt: 1, textAlign: 'center', color: 'text.secondary' }}>
                  Abra o WhatsApp no seu celular, acesse Configurações &gt; Dispositivos conectados &gt; Conectar um dispositivo
                </Typography>
                <Button 
                  startIcon={<Refresh />} 
                  onClick={initializeWhatsApp} 
                  sx={{ mt: 2 }}
                >
                  Gerar novo QR Code
                </Button>
              </Box>
            )}
          </Paper>
        </Grid>
        
        {/* Token Balance */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <AccountBalance color="primary" sx={{ mr: 1 }} />
                <Typography component="h2" variant="h6" color="primary">
                  Saldo de Tokens
                </Typography>
              </Box>
              <Typography component="h1" variant="h3" sx={{ mt: 2 }}>
                {tokenBalance}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Cada mensagem de texto = 1 token
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Cada mensagem com mídia = 2 tokens
              </Typography>
              <Box sx={{ mt: 2 }}>
                <Button variant="contained" color="primary" disabled>
                  Comprar mais tokens
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        {/* Contact List Uploader */}
        <Grid item xs={12} md={6}>
          <ContactListUploader 
            onContactsLoaded={(contactList) => {
              setContacts(contactList);
              toast.success(`${contactList.length} contatos carregados`);
            }} 
          />
        </Grid>
        
        {/* Message Composer */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography component="h2" variant="h6" color="primary" gutterBottom>
              Compor Mensagem
            </Typography>
            
            {/* Contact Selection */}
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle1" gutterBottom>
                Destinatários ({selectedContacts.length} selecionados)
              </Typography>
              
              {contacts.length > 0 ? (
                <>
                  <Box sx={{ display: 'flex', mb: 1 }}>
                    <Button size="small" onClick={handleSelectAllContacts}>
                      Selecionar Todos
                    </Button>
                    <Button size="small" onClick={handleClearSelectedContacts}>
                      Limpar Seleção
                    </Button>
                  </Box>
                  
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', mb: 2 }}>
                    <FormControl fullWidth>
                      <InputLabel>Selecione os Contatos</InputLabel>
                      <Select
                        multiple
                        value={selectedContacts}
                        onChange={(e) => setSelectedContacts(e.target.value)}
                        renderValue={(selected) => (
                          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                            {selected.map((value) => (
                              <Chip key={value} label={value} />
                            ))}
                          </Box>
                        )}
                      >
                        {contacts.map((contact) => (
                          <MenuItem key={contact.number} value={contact.number}>
                            {contact.name ? `${contact.name} (${contact.number})` : contact.number}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </Box>
                </>
              ) : (
                <Alert severity="info">
                  Carregue uma lista de contatos primeiro
                </Alert>
              )}
            </Box>
            
            <Divider sx={{ my: 2 }} />
            
            {/* Message Text */}
            <TextField
              label="Mensagem"
              multiline
              rows={4}
              fullWidth
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              margin="normal"
              placeholder="Digite a mensagem que deseja enviar..."
            />
            
            {/* File Upload */}
            <Box sx={{ mt: 2, mb: 3 }}>
              <Typography variant="subtitle1" gutterBottom>
                Anexar Arquivo (opcional)
              </Typography>
              
              {files.length > 0 ? (
                <Box sx={{ mt: 2, mb: 2 }}>
                  <Paper 
                    elevation={1}
                    sx={{ 
                      p: 1, 
                      display: 'flex', 
                      alignItems: 'center',
                      justifyContent: 'space-between'
                    }}
                  >
                    <Typography variant="body2">
                      {files[0].name} ({(files[0].size / 1024).toFixed(1)} KB)
                    </Typography>
                    <IconButton size="small" onClick={removeFile}>
                      <Close fontSize="small" />
                    </IconButton>
                  </Paper>
                </Box>
              ) : (
                <Box 
                  {...getRootProps()} 
                  sx={{ 
                    border: '2px dashed #ccc', 
                    borderRadius: 2, 
                    p: 3, 
                    textAlign: 'center',
                    cursor: 'pointer',
                    '&:hover': {
                      bgcolor: 'rgba(0, 0, 0, 0.03)'
                    }
                  }}
                >
                  <input {...getInputProps()} />
                  <CloudUpload fontSize="large" color="primary" />
                  <Typography variant="body1" sx={{ mt: 1 }}>
                    Arraste um arquivo ou clique para selecionar
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Imagens, PDFs, documentos, áudios ou vídeos (máx. 16MB)
                  </Typography>
                </Box>
              )}
            </Box>
            
            {/* Token cost calculation */}
            <Box sx={{ mb: 3, mt: 2 }}>
              <Alert severity="info">
                <Typography variant="body2">
                  Custo estimado: <strong>{selectedContacts.length * (files.length > 0 ? 2 : 1)} tokens</strong> ({selectedContacts.length} contatos × {files.length > 0 ? '2 tokens por mídia' : '1 token por texto'})
                </Typography>
              </Alert>
            </Box>
            
            {/* Send Button */}
            <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
              <Button
                variant="contained"
                color="primary"
                startIcon={isSending ? <CircularProgress size={20} color="inherit" /> : <Send />}
                onClick={handleSendMessage}
                disabled={
                  isSending || 
                  selectedContacts.length === 0 || 
                  whatsappStatus !== 'authenticated' ||
                  (!message && files.length === 0) ||
                  tokenBalance < (selectedContacts.length * (files.length > 0 ? 2 : 1))
                }
              >
                {isSending ? 'Enviando...' : 'Enviar Mensagem'}
              </Button>
            </Box>
          </Paper>
        </Grid>
        
        {/* Token History */}
        <Grid item xs={12}>
          <TokenHistory />
        </Grid>
      </Grid>
    </Container>
  );
};

export default ClientDashboard;