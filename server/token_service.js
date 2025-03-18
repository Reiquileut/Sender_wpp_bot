/**
 * token_service.js
 * 
 * Serviço de autenticação e gerenciamento de tokens para o WhatsApp Messenger API.
 * Implementa:
 * - Autenticação de usuários
 * - Verificação de JWT
 * - Controle de uso de tokens
 * - Validação de limites de mensagens
 */

const crypto = require('crypto');
const jwt = require('jsonwebtoken');
const fs = require('fs');
const path = require('path');

// Configurações
const JWT_SECRET = process.env.JWT_SECRET || 'whatsapp-messenger-secret-jwt-key-change-in-production';
const JWT_EXPIRES_IN = '7d';
const TOKENS_DIR = path.join(process.cwd(), 'data', 'tokens');
const USERS_FILE = path.join(process.cwd(), 'data', 'users.json');

// Garantir que os diretórios existam
try {
    fs.mkdirSync(path.join(process.cwd(), 'data'), { recursive: true });
    fs.mkdirSync(TOKENS_DIR, { recursive: true });
    
    // Criar arquivo de usuários se não existir
    if (!fs.existsSync(USERS_FILE)) {
        fs.writeFileSync(USERS_FILE, JSON.stringify({
            users: [],
            nextId: 1
        }, null, 2));
    }
} catch (err) {
    console.error('Erro ao criar diretórios ou arquivos de dados:', err);
}

/**
 * Classe TokenService - Gerencia autenticação e tokens
 */
class TokenService {
    constructor() {
        this.loadUsers();
    }

    /**
     * Carrega usuários do arquivo
     */
    loadUsers() {
        try {
            const data = fs.readFileSync(USERS_FILE, 'utf8');
            this.usersData = JSON.parse(data);
        } catch (err) {
            console.error('Erro ao carregar usuários:', err);
            this.usersData = { users: [], nextId: 1 };
        }
    }

    /**
     * Salva usuários no arquivo
     */
    saveUsers() {
        try {
            fs.writeFileSync(USERS_FILE, JSON.stringify(this.usersData, null, 2));
        } catch (err) {
            console.error('Erro ao salvar usuários:', err);
        }
    }

    /**
     * Autentica um usuário e retorna um token JWT
     * @param {string} username Nome de usuário
     * @param {string} password Senha
     * @returns {Object} Objeto com token e dados do usuário ou erro
     */
    authenticate(username, password) {
        const user = this.usersData.users.find(u => u.username === username);
        
        if (!user) {
            return { success: false, error: 'Usuário não encontrado' };
        }

        // Verifica a senha (hash com salt)
        const hashedPassword = this.hashPassword(password, user.salt);
        if (hashedPassword !== user.password) {
            return { success: false, error: 'Senha incorreta' };
        }

        // Gera token JWT
        const token = jwt.sign(
            { 
                id: user.id, 
                username: user.username,
                role: user.role
            }, 
            JWT_SECRET, 
            { expiresIn: JWT_EXPIRES_IN }
        );

        return {
            success: true,
            token,
            user: {
                id: user.id,
                username: user.username,
                email: user.email,
                role: user.role,
                name: user.name
            }
        };
    }

    /**
     * Verifica se um token JWT é válido
     * @param {string} token Token JWT
     * @returns {Object} Payload do token ou null se inválido
     */
    verifyToken(token) {
        try {
            return jwt.verify(token, JWT_SECRET);
        } catch (err) {
            console.error('Erro ao verificar token:', err.message);
            return null;
        }
    }

    /**
     * Cria um novo usuário
     * @param {Object} userData Dados do usuário
     * @returns {Object} Resultado da operação
     */
    createUser(userData) {
        // Verifica se usuário já existe
        if (this.usersData.users.some(u => u.username === userData.username)) {
            return { success: false, error: 'Nome de usuário já existe' };
        }

        // Gera salt e hash para a senha
        const salt = crypto.randomBytes(16).toString('hex');
        const hashedPassword = this.hashPassword(userData.password, salt);

        // Cria o usuário
        const newUser = {
            id: this.usersData.nextId++,
            username: userData.username,
            password: hashedPassword,
            salt: salt,
            email: userData.email,
            name: userData.name || userData.username,
            role: userData.role || 'user',
            tokenBalance: userData.initialTokens || 0,
            created: new Date().toISOString(),
            lastLogin: null
        };

        // Adiciona à lista e salva
        this.usersData.users.push(newUser);
        this.saveUsers();

        // Cria arquivo de uso de tokens
        this.initializeTokenUsage(newUser.id);

        return {
            success: true,
            user: {
                id: newUser.id,
                username: newUser.username,
                email: newUser.email,
                role: newUser.role,
                name: newUser.name,
                tokenBalance: newUser.tokenBalance
            }
        };
    }

    /**
     * Inicializa arquivo de uso de tokens para um usuário
     * @param {number} userId ID do usuário
     */
    initializeTokenUsage(userId) {
        const tokenFile = path.join(TOKENS_DIR, `${userId}.json`);
        
        if (!fs.existsSync(tokenFile)) {
            fs.writeFileSync(tokenFile, JSON.stringify({
                userId,
                usage: [],
                monthlyUsage: {},
                lastUpdated: new Date().toISOString()
            }, null, 2));
        }
    }

    /**
     * Hash de senha com salt
     * @param {string} password Senha em texto plano
     * @param {string} salt Salt para o hash
     * @returns {string} Senha hasheada
     */
    hashPassword(password, salt) {
        return crypto
            .pbkdf2Sync(password, salt, 1000, 64, 'sha512')
            .toString('hex');
    }

    /**
     * Obtém o saldo de tokens de um usuário
     * @param {number} userId ID do usuário
     * @returns {number} Saldo de tokens
     */
    getTokenBalance(userId) {
        const user = this.usersData.users.find(u => u.id === userId);
        return user ? user.tokenBalance : 0;
    }

    /**
     * Adiciona tokens ao saldo de um usuário
     * @param {number} userId ID do usuário
     * @param {number} amount Quantidade de tokens
     * @returns {boolean} Sucesso da operação
     */
    addTokens(userId, amount) {
        const userIndex = this.usersData.users.findIndex(u => u.id === userId);
        
        if (userIndex === -1) {
            return false;
        }

        this.usersData.users[userIndex].tokenBalance += amount;
        this.saveUsers();

        return true;
    }

    /**
     * Consome tokens do saldo de um usuário
     * @param {number} userId ID do usuário
     * @param {number} amount Quantidade de tokens
     * @param {string} operation Tipo de operação
     * @returns {boolean} Sucesso da operação
     */
    consumeTokens(userId, amount, operation) {
        const userIndex = this.usersData.users.findIndex(u => u.id === userId);
        
        if (userIndex === -1) {
            return false;
        }

        // Verifica se há saldo suficiente
        if (this.usersData.users[userIndex].tokenBalance < amount) {
            return false;
        }

        // Debita os tokens
        this.usersData.users[userIndex].tokenBalance -= amount;
        this.saveUsers();

        // Registra o uso
        this.recordTokenUsage(userId, amount, operation);

        return true;
    }

    /**
     * Registra o uso de tokens
     * @param {number} userId ID do usuário
     * @param {number} amount Quantidade de tokens
     * @param {string} operation Tipo de operação
     */
    recordTokenUsage(userId, amount, operation) {
        const tokenFile = path.join(TOKENS_DIR, `${userId}.json`);
        
        try {
            let usageData;
            
            if (fs.existsSync(tokenFile)) {
                usageData = JSON.parse(fs.readFileSync(tokenFile, 'utf8'));
            } else {
                usageData = {
                    userId,
                    usage: [],
                    monthlyUsage: {},
                    lastUpdated: new Date().toISOString()
                };
            }

            // Adiciona registro de uso
            const now = new Date();
            const timestamp = now.toISOString();
            const yearMonth = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;

            usageData.usage.push({
                timestamp,
                operation,
                tokens: amount
            });

            // Atualiza uso mensal
            if (!usageData.monthlyUsage[yearMonth]) {
                usageData.monthlyUsage[yearMonth] = 0;
            }
            usageData.monthlyUsage[yearMonth] += amount;

            // Limita o histórico de uso a 1000 entradas
            if (usageData.usage.length > 1000) {
                usageData.usage = usageData.usage.slice(usageData.usage.length - 1000);
            }

            usageData.lastUpdated = timestamp;

            // Salva atualizações
            fs.writeFileSync(tokenFile, JSON.stringify(usageData, null, 2));

        } catch (err) {
            console.error(`Erro ao registrar uso de tokens para usuário ${userId}:`, err);
        }
    }

    /**
     * Obtém o histórico de uso de tokens de um usuário
     * @param {number} userId ID do usuário
     * @returns {Object} Histórico de uso
     */
    getTokenUsage(userId) {
        const tokenFile = path.join(TOKENS_DIR, `${userId}.json`);
        
        try {
            if (fs.existsSync(tokenFile)) {
                return JSON.parse(fs.readFileSync(tokenFile, 'utf8'));
            }
        } catch (err) {
            console.error(`Erro ao ler uso de tokens para usuário ${userId}:`, err);
        }

        return {
            userId,
            usage: [],
            monthlyUsage: {},
            lastUpdated: new Date().toISOString()
        };
    }

    /**
     * Verifica se o usuário tem tokens suficientes para uma operação
     * @param {number} userId ID do usuário
     * @param {number} requiredTokens Tokens necessários
     * @returns {boolean} Se há tokens suficientes
     */
    hasEnoughTokens(userId, requiredTokens) {
        const balance = this.getTokenBalance(userId);
        return balance >= requiredTokens;
    }

    /**
     * Calcula tokens necessários para enviar mensagens
     * @param {number} messageCount Número de mensagens
     * @param {number} fileCount Número de arquivos
     * @returns {number} Total de tokens necessários
     */
    calculateRequiredTokens(messageCount, fileCount = 0) {
        // Exemplo de cálculo: 1 token por mensagem, 2 tokens por arquivo
        return messageCount + (fileCount * 2);
    }
}

module.exports = new TokenService();
