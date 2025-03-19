// src/components/TokenHistory.js
import React, { useState, useEffect } from 'react';
import { 
  Paper, Typography, Box, CircularProgress, Chip,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  TablePagination
} from '@mui/material';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import { API_URL } from '../config';
import { toast } from 'react-toastify';
import moment from 'moment';

const TokenHistory = () => {
  const { token } = useAuth();
  const [loading, setLoading] = useState(true);
  const [transactions, setTransactions] = useState([]);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  
  useEffect(() => {
    const fetchTokenHistory = async () => {
      setLoading(true);
      try {
        const response = await axios.get(`${API_URL}/tokens/history`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        setTransactions(response.data);
      } catch (error) {
        console.error('Error fetching token history:', error);
        toast.error('Erro ao carregar histórico de tokens');
      } finally {
        setLoading(false);
      }
    };
    
    fetchTokenHistory();
  }, [token]);
  
  // Handle page change
  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };
  
  // Handle rows per page change
  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };
  
  // Get chip color based on transaction type
  const getChipColor = (type, amount) => {
    if (type === 'purchase' || (type === 'adjustment' && amount > 0)) {
      return 'success';
    } else if (type === 'consumption' || (type === 'adjustment' && amount < 0)) {
      return 'error';
    } else if (type === 'refund') {
      return 'warning';
    }
    return 'default';
  };
  
  // Get human readable transaction type
  const getTransactionTypeText = (type) => {
    switch (type) {
      case 'purchase':
        return 'Compra';
      case 'consumption':
        return 'Consumo';
      case 'refund':
        return 'Reembolso';
      case 'adjustment':
        return 'Ajuste';
      default:
        return type;
    }
  };

  return (
    <Paper sx={{ p: 3 }}>
      <Typography component="h2" variant="h6" color="primary" gutterBottom>
        Histórico de Tokens
      </Typography>
      
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
          <CircularProgress />
        </Box>
      ) : (
        <>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Data</TableCell>
                  <TableCell>Tipo</TableCell>
                  <TableCell align="right">Quantidade</TableCell>
                  <TableCell align="right">Saldo Após</TableCell>
                  <TableCell>Descrição</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {transactions.length > 0 ? (
                  transactions
                    .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                    .map((transaction) => (
                      <TableRow key={transaction._id}>
                        <TableCell>
                          {moment(transaction.createdAt).format('DD/MM/YYYY HH:mm')}
                        </TableCell>
                        <TableCell>
                          <Chip 
                            label={getTransactionTypeText(transaction.type)}
                            color={getChipColor(transaction.type, transaction.amount)}
                            size="small"
                          />
                        </TableCell>
                        <TableCell 
                          align="right"
                          sx={{ 
                            color: transaction.amount > 0 ? 'success.main' : 'error.main',
                            fontWeight: 'bold'
                          }}
                        >
                          {transaction.amount > 0 ? '+' : ''}{transaction.amount}
                        </TableCell>
                        <TableCell align="right">
                          {transaction.balanceAfter}
                        </TableCell>
                        <TableCell>
                          {transaction.description || '-'}
                        </TableCell>
                      </TableRow>
                    ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={5} align="center">
                      Nenhuma transação de token encontrada
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
          
          <TablePagination
            rowsPerPageOptions={[10, 25, 50]}
            component="div"
            count={transactions.length}
            rowsPerPage={rowsPerPage}
            page={page}
            onPageChange={handleChangePage}
            onRowsPerPageChange={handleChangeRowsPerPage}
            labelRowsPerPage="Linhas por página:"
            labelDisplayedRows={({ from, to, count }) => `${from}-${to} de ${count}`}
          />
        </>
      )}
    </Paper>
  );
};

export default TokenHistory;