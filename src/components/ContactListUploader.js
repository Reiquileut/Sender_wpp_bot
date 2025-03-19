// src/components/ContactListUploader.js
import React, { useState } from 'react';
import { 
  Paper, Typography, Box, Button, Alert,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  CircularProgress, IconButton
} from '@mui/material';
import { CloudUpload, Delete, CheckCircle, Error } from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import * as XLSX from 'xlsx';
import Papa from 'papaparse';
import { toast } from 'react-toastify';

const ContactListUploader = ({ onContactsLoaded }) => {
  const [loading, setLoading] = useState(false);
  const [contacts, setContacts] = useState([]);
  const [fileInfo, setFileInfo] = useState(null);
  const [validationErrors, setValidationErrors] = useState([]);
  
  // Handle file upload
  const { getRootProps, getInputProps } = useDropzone({
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls']
    },
    maxFiles: 1,
    onDrop: acceptedFiles => {
      handleFileUpload(acceptedFiles[0]);
    }
  });
  
  // Process uploaded file
  const handleFileUpload = async (file) => {
    setLoading(true);
    setContacts([]);
    setValidationErrors([]);
    
    try {
      setFileInfo({
        name: file.name,
        size: (file.size / 1024).toFixed(2) + ' KB',
        type: file.type
      });
      
      const fileExtension = file.name.split('.').pop().toLowerCase();
      let parsedContacts = [];
      
      if (fileExtension === 'csv') {
        // Parse CSV
        const text = await file.text();
        const result = Papa.parse(text, {
          header: true,
          skipEmptyLines: true
        });
        
        if (result.data && result.data.length > 0) {
          parsedContacts = processContactData(result.data);
        } else {
          throw new Error('Arquivo CSV vazio ou inválido');
        }
      } else if (['xlsx', 'xls'].includes(fileExtension)) {
        // Parse Excel
        const arrayBuffer = await file.arrayBuffer();
        const workbook = XLSX.read(arrayBuffer);
        const worksheet = workbook.Sheets[workbook.SheetNames[0]];
        const data = XLSX.utils.sheet_to_json(worksheet);
        
        if (data && data.length > 0) {
          parsedContacts = processContactData(data);
        } else {
          throw new Error('Arquivo Excel vazio ou inválido');
        }
      }
      
      // Validate contacts
      const { validContacts, errors } = validateContacts(parsedContacts);
      
      setContacts(validContacts);
      setValidationErrors(errors);
      
      if (validContacts.length > 0) {
        toast.success(`${validContacts.length} contatos carregados com sucesso`);
        onContactsLoaded(validContacts);
      }
      
      if (errors.length > 0) {
        toast.warning(`${errors.length} contatos com problemas detectados`);
      }
    } catch (error) {
      console.error('Error processing file:', error);
      toast.error(`Erro ao processar arquivo: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };
  
  // Process contact data from various formats
  const processContactData = (data) => {
    return data.map((row, index) => {
      // Try to get phone number from common column names
      const possiblePhoneColumns = ['phone', 'telefone', 'celular', 'number', 'mobile', 'whatsapp', 'tel'];
      const possibleNameColumns = ['name', 'nome', 'contact', 'contato', 'pessoa'];
      
      // Find the phone column
      let phoneValue = null;
      let phoneColumn = null;
      
      for (const column of possiblePhoneColumns) {
        if (row[column] !== undefined) {
          phoneValue = row[column];
          phoneColumn = column;
          break;
        }
      }
      
      // If no phone column found, try the first column
      if (!phoneValue) {
        const firstColumn = Object.keys(row)[0];
        if (firstColumn) {
          phoneValue = row[firstColumn];
          phoneColumn = firstColumn;
        }
      }
      
      // Find the name column
      let nameValue = null;
      
      for (const column of possibleNameColumns) {
        if (row[column] !== undefined) {
          nameValue = row[column];
          break;
        }
      }
      
      // If we found a phone but no name, look for the second column
      if (phoneValue && !nameValue && Object.keys(row).length > 1) {
        const columns = Object.keys(row);
        const secondColumn = columns.find(col => col !== phoneColumn);
        if (secondColumn) {
          nameValue = row[secondColumn];
        }
      }
      
      return {
        id: index,
        number: phoneValue ? String(phoneValue).trim() : null,
        name: nameValue ? String(nameValue).trim() : null
      };
    });
  };
  
  // Validate contacts
  const validateContacts = (contacts) => {
    const validContacts = [];
    const errors = [];
    
    contacts.forEach(contact => {
      if (!contact.number) {
        errors.push({
          id: contact.id,
          message: 'Número de telefone vazio',
          contact
        });
        return;
      }
      
      // Clean the number
      let number = String(contact.number).replace(/\D/g, '');
      
      // Check if it's a valid number format
      if (number.length < 8) {
        errors.push({
          id: contact.id,
          message: 'Número de telefone muito curto',
          contact
        });
        return;
      }
      
      // Format the number (for Brazil as default, but could be expanded)
      // If it doesn't have country code, add Brazil's
      if (number.length <= 11) {
        number = '55' + number;
      }
      
      // Add the formatted contact to valid contacts
      validContacts.push({
        ...contact,
        number
      });
    });
    
    return { validContacts, errors };
  };
  
  // Clear all contacts
  const clearContacts = () => {
    setContacts([]);
    setFileInfo(null);
    setValidationErrors([]);
    toast.info('Lista de contatos limpa');
  };

  return (
    <Paper sx={{ p: 3 }}>
      <Typography component="h2" variant="h6" color="primary" gutterBottom>
        Importar Contatos
      </Typography>
      
      {!fileInfo ? (
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
            Arraste um arquivo CSV ou Excel ou clique para selecionar
          </Typography>
          <Typography variant="caption" color="text.secondary">
            O arquivo deve conter uma coluna com números de telefone
          </Typography>
        </Box>
      ) : (
        <>
          <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box>
              <Typography variant="subtitle1" gutterBottom>
                <strong>Arquivo:</strong> {fileInfo.name}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {fileInfo.size} • {contacts.length} contatos carregados
              </Typography>
            </Box>
            <Button 
              startIcon={<Delete />}
              onClick={clearContacts}
              color="secondary"
            >
              Limpar
            </Button>
          </Box>
          
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <CircularProgress />
            </Box>
          ) : (
            <>
              {validationErrors.length > 0 && (
                <Alert severity="warning" sx={{ mb: 2 }}>
                  {validationErrors.length} contatos com problemas foram encontrados
                </Alert>
              )}
              
              <TableContainer sx={{ maxHeight: 300 }}>
                <Table stickyHeader size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Status</TableCell>
                      <TableCell>Nome</TableCell>
                      <TableCell>Número</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {contacts.slice(0, 100).map((contact) => {
                      const hasError = validationErrors.some(e => e.id === contact.id);
                      
                      return (
                        <TableRow key={contact.id}>
                          <TableCell>
                            {hasError ? (
                              <Error fontSize="small" color="error" />
                            ) : (
                              <CheckCircle fontSize="small" color="success" />
                            )}
                          </TableCell>
                          <TableCell>{contact.name || '(Sem nome)'}</TableCell>
                          <TableCell>{contact.number}</TableCell>
                        </TableRow>
                      );
                    })}
                    
                    {validationErrors.slice(0, 100)
                      .filter(error => !contacts.some(c => c.id === error.id))
                      .map((error) => (
                        <TableRow key={`error-${error.id}`}>
                          <TableCell>
                            <Error fontSize="small" color="error" />
                          </TableCell>
                          <TableCell>{error.contact.name || '(Sem nome)'}</TableCell>
                          <TableCell>
                            <Typography color="error">
                              {error.contact.number || '(Vazio)'} - {error.message}
                            </Typography>
                          </TableCell>
                        </TableRow>
                      ))}
                      
                    {contacts.length === 0 && validationErrors.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={3} align="center">
                          Nenhum contato encontrado no arquivo
                        </TableCell>
                      </TableRow>
                    )}
                    
                    {contacts.length > 100 && (
                      <TableRow>
                        <TableCell colSpan={3} align="center">
                          Mostrando 100 de {contacts.length} contatos
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </>
          )}
        </>
      )}
    </Paper>
  );
};

export default ContactListUploader;