// src/contexts/AuthContext.js
import React, { createContext, useState, useContext, useEffect } from 'react';
import axios from 'axios';
import { API_URL } from '../config';
import { toast } from 'react-toastify';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);
  
  // Check if user is logged in on initial load
  useEffect(() => {
    const checkUserLoggedIn = async () => {
      if (token) {
        try {
          const response = await axios.get(`${API_URL}/auth/me`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          
          setUser(response.data);
        } catch (error) {
          console.error('Error validating token:', error);
          // If token is invalid, remove it
          localStorage.removeItem('token');
          setToken(null);
        }
      }
      
      setLoading(false);
    };
    
    checkUserLoggedIn();
  }, [token]);
  
  // Login function
  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API_URL}/auth/login`, {
        email,
        password
      });
      
      const { token: authToken, user: userData } = response.data;
      
      localStorage.setItem('token', authToken);
      setToken(authToken);
      setUser(userData);
      
      return { success: true };
    } catch (error) {
      console.error('Login error:', error);
      return { 
        success: false, 
        message: error.response?.data?.message || 'Erro ao realizar login'
      };
    }
  };
  
  // Register function
  const register = async (name, email, password) => {
    try {
      const response = await axios.post(`${API_URL}/auth/register`, {
        name,
        email,
        password
      });
      
      return { success: true };
    } catch (error) {
      console.error('Registration error:', error);
      return { 
        success: false, 
        message: error.response?.data?.message || 'Erro ao realizar cadastro'
      };
    }
  };
  
  // Logout function
  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    toast.info('Desconectado com sucesso');
  };
  
  // Update user info
  const updateUser = async (userData) => {
    try {
      const response = await axios.put(`${API_URL}/users/me`, userData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setUser(response.data);
      toast.success('Perfil atualizado com sucesso');
      
      return { success: true };
    } catch (error) {
      console.error('Profile update error:', error);
      toast.error(error.response?.data?.message || 'Erro ao atualizar perfil');
      
      return { 
        success: false, 
        message: error.response?.data?.message || 'Erro ao atualizar perfil'
      };
    }
  };
  
  // Change password
  const changePassword = async (currentPassword, newPassword) => {
    try {
      await axios.put(`${API_URL}/users/password`, 
        { currentPassword, newPassword }, 
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      toast.success('Senha alterada com sucesso');
      return { success: true };
    } catch (error) {
      console.error('Password change error:', error);
      
      return { 
        success: false, 
        message: error.response?.data?.message || 'Erro ao alterar senha'
      };
    }
  };
  
  // Request password reset
  const requestPasswordReset = async (email) => {
    try {
      await axios.post(`${API_URL}/auth/forgot-password`, { email });
      
      toast.success('Email de recuperação enviado. Verifique sua caixa de entrada.');
      return { success: true };
    } catch (error) {
      console.error('Password reset request error:', error);
      
      return { 
        success: false, 
        message: error.response?.data?.message || 'Erro ao solicitar recuperação de senha'
      };
    }
  };
  
  // Reset password with token
  const resetPassword = async (token, newPassword) => {
    try {
      await axios.post(`${API_URL}/auth/reset-password`, { 
        token, 
        password: newPassword 
      });
      
      toast.success('Senha redefinida com sucesso. Você já pode fazer login.');
      return { success: true };
    } catch (error) {
      console.error('Password reset error:', error);
      
      return { 
        success: false, 
        message: error.response?.data?.message || 'Erro ao redefinir senha'
      };
    }
  };

  return (
    <AuthContext.Provider value={{ 
      user, 
      token,
      loading,
      login,
      register,
      logout,
      updateUser,
      changePassword,
      requestPasswordReset,
      resetPassword
    }}>
      {children}
    </AuthContext.Provider>
  );
};