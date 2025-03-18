# Referência de Comandos - WhatsApp Messenger CLI

Este documento fornece uma referência completa para todos os comandos disponíveis via terminal Linux na versão escalável do WhatsApp Messenger.

## Sumário

1. [Instalação](#instalação)
2. [Comandos de Autenticação](#comandos-de-autenticação)
3. [Comandos de Mensagem](#comandos-de-mensagem)
4. [Comandos de Análise de Números](#comandos-de-análise-de-números)
5. [Comandos de Gerenciamento de Serviço](#comandos-de-gerenciamento-de-serviço)
6. [Comandos de Sistema de Tokens](#comandos-de-sistema-de-tokens)
7. [Opções Avançadas](#opções-avançadas)
8. [Exemplos de Uso](#exemplos-de-uso)
9. [Troubleshooting](#troubleshooting)

---

## Instalação

### Pré-requisitos

- Python 3.7+ 
- Node.js 14.0+
- Docker e Docker Compose (para instalação em container)

### Instalação via Terminal

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/whatsapp-messenger.git
cd whatsapp-messenger

# Instale dependências Python
pip install -r requirements.txt

# Instale dependências Node
cd server
npm install
cd ..

# Torne o script CLI executável
chmod +x whatsapp_cli.py
```

### Instalação com Docker

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/whatsapp-messenger.git
cd whatsapp-messenger

# Configure variáveis de ambiente (opcional)
cp .env.example .env
nano .env

# Inicie os containers
docker-compose up -d
```

---

## Comandos de Autenticação

### Verificar Status

Verifica o status da conexão com o WhatsApp.

```bash
./whatsapp_cli.py status
```

**Saída:**
- ✅ WhatsApp conectado e pronto para uso
- ⚠️ Aguardando autenticação. Use o comando 'login' para scanear o QR code.
- ❌ Servidor não disponível.

### Login

Gera e exibe um QR code para autenticação no WhatsApp.

```bash
./whatsapp_cli.py login
```

**Saída:**
- Exibe um QR code para ser escaneado com o WhatsApp
- ✅ WhatsApp conectado com sucesso!

### Reiniciar Sessão

Reinicia a sessão do WhatsApp, desconectando o dispositivo atual.

```bash
./whatsapp_cli.py reset
```

**Saída:**
- 🔄 Reiniciando sessão do WhatsApp...
- ✅ Sessão reiniciada com sucesso!

### Autenticação API (Usuários)

Para serviços API, obtenha um token de autenticação:

```bash
# Formato
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"seu_usuario","password":"sua_senha"}'
```

**Resposta:**
```json
{
  "success": true,
  "token": "seu_jwt_token",
  "user": {
    "id": 1,
    "username": "seu_usuario",
    "role": "admin"
  }
}
```

---

## Comandos de Mensagem

### Enviar Mensagem de Texto

Envia uma mensagem de texto para um número de telefone.

```bash
./whatsapp_cli.py send-text --to NUMERO --message "Sua mensagem aqui"
```

**Opções:**
- `--to, -t`: Número do destinatário (obrigatório)
- `--message, -m`: Texto da mensagem (obrigatório)

**Saída:**
- ✅ Mensagem enviada com sucesso! ID: msg123456

### Enviar Arquivo

Envia um arquivo para um número de telefone.

```bash
./whatsapp_cli.py send-file --to NUMERO --file caminho/do/arquivo.pdf --caption "Legenda do arquivo"
```

**Opções:**
- `--to, -t`: Número do destinatário (obrigatório)
- `--file, -f`: Caminho do arquivo (obrigatório)
- `--caption, -c`: Legenda do arquivo (opcional)

**Saída:**
- ✅ Arquivo enviado com sucesso! ID: msg123456

### Envio em Lote

Envia mensagens para múltiplos destinatários a partir de um arquivo CSV/XLSX.

```bash
./whatsapp_cli.py send-batch --file contatos.csv --message "Mensagem para todos" --files arquivo1.pdf arquivo2.jpg --interval 5
```

**Opções:**
- `--file, -f`: Arquivo CSV/XLSX com contatos (obrigatório)
- `--message, -m`: Texto da mensagem (opcional)
- `--files`: Arquivos para anexar (opcional)
- `--interval, -i`: Intervalo entre mensagens em segundos (padrão: 3)
- `--no-random`: Desativa variação aleatória no intervalo

**Formato do CSV/XLSX:**
O arquivo deve conter os números na primeira coluna. Não são necessários cabeçalhos.

**Saída:**
- 📋 Carregados X contatos do arquivo.
- 📊 Exibe estatísticas de progresso durante o envio
- 📄 Relatório final e exportação de falhas se houver

---

## Comandos de Análise de Números

### Analisar Número

Analisa o formato de um número de telefone.

```bash
./whatsapp_cli.py analyze --number "551199887766"
```

**Opções:**
- `--number, -n`: Número de telefone para analisar (obrigatório)

**Saída:**
```
📱 Análise de Número:
Número original: 551199887766
Número limpo: 551199887766
Número formatado: 551199887766
País: Brasil
Código do país: 55
Formato reconhecido: Sim
```

### Analisar Lote de Números

Analisa um lote de números de telefone a partir de um arquivo.

```bash
./whatsapp_cli.py batch-analyze --file contatos.csv
```

**Opções:**
- `--file, -f`: Arquivo CSV/XLSX com números de telefone (obrigatório)

**Saída:**
- 📋 Carregados X números do arquivo.
- 📊 Estatísticas gerais sobre os números
- 🌎 Distribuição por país
- 📄 Exportação da análise para CSV

---

## Comandos de Gerenciamento de Serviço

### Iniciar Servidor

Inicia o servidor WhatsApp em segundo plano.

```bash
./whatsapp_cli.py start-server --port 3001
```

**Opções:**
- `--port, -p`: Porta para o servidor (opcional, padrão: 3000)

**Saída:**
- 🚀 Iniciando servidor WhatsApp...
- ✅ Servidor iniciado com PID: 12345

### Parar Servidor

Para o servidor WhatsApp.

```bash
./whatsapp_cli.py stop-server
```

**Saída:**
- 🛑 Parando servidor (PID: 12345)...
- ✅ Servidor parado com sucesso.

### Verificar Status do Servidor

Verifica o status do servidor WhatsApp.

```bash
./whatsapp_cli.py status-server
```

**Saída:**
- (Mesma saída do comando `status`)

---

## Comandos de Sistema de Tokens

### Verificar Saldo de Tokens

Verifica os tokens disponíveis para o usuário atual.

```bash
./whatsapp_cli.py tokens-status
```

**Saída:**
```
🪙 Sistema de Tokens
Tokens disponíveis: 1000
Tokens usados este mês: 250
Validade: 31/12/2025
```

### Adicionar Tokens (API Admin)

Adiciona tokens à conta de um usuário (requer privilégios de admin).

```bash
# Formato API
curl -X POST http://localhost:3000/api/admin/tokens/add \
  -H "Authorization: Bearer seu_token_admin" \
  -H "Content-Type: application/json" \
  -d '{"userId":123,"amount":500,"note":"Compra mensal"}'
```

### Consumo de Tokens

O consumo de tokens é automático com base no tipo de mensagem:

- 1 token por mensagem de texto
- 2 tokens por arquivo enviado
- Multiplicado pelo número de destinatários

---

## Opções Avançadas

### Configuração de Webhook

Configure webhooks para receber notificações de mensagens recebidas:

```bash
# Formato API
curl -X POST http://localhost:3000/api/webhook/configure \
  -H "Authorization: Bearer seu_token" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://seu-servidor.com/webhook","events":["message","status"]}'
```

### Personalização de Intervalos

Para envios em lote com intervalos personalizados:

```bash
./whatsapp_cli.py send-batch --file contatos.csv --message "Mensagem" --interval 10 --no-random
```

### Exportação de Logs

Exporte logs detalhados para análise:

```bash
# Logs do servidor
docker-compose logs whatsapp-api > server_logs.txt

# Logs do CLI
cat whatsapp_cli.log > cli_logs.txt
```

---

## Exemplos de Uso

### Fluxo Básico de Instalação e Uso

```bash
# 1. Clone e configure
git clone https://github.com/seu-usuario/whatsapp-messenger.git
cd whatsapp-messenger
pip install -r requirements.txt

# 2. Inicie o servidor
./whatsapp_cli.py start-server

# 3. Faça login no WhatsApp
./whatsapp_cli.py login
# Escaneie o QR code

# 4. Envie uma mensagem
./whatsapp_cli.py send-text --to 551199887766 --message "Olá, este é um teste!"

# 5. Envie para múltiplos contatos
./whatsapp_cli.py send-batch --file contatos.csv --message "Mensagem em massa"
```

### Uso com Docker

```bash
# 1. Inicie os containers
docker-compose up -d

# 2. Obtenha o QR code para login
curl http://localhost:3000/api/qrcode > qrcode.txt

# 3. Use a API para enviar mensagens
curl -X POST http://localhost:3000/api/send-message \
  -H "Authorization: Bearer seu_token" \
  -H "Content-Type: application/json" \
  -d '{"number":"551199887766","message":"Teste via API"}'
```

---

## Troubleshooting

### Servidor não inicia

**Problema:** Ao executar `start-server`, o servidor não inicia.

**Solução:**
1. Verifique se Node.js está instalado: `node --version`
2. Verifique se a porta já está em uso: `netstat -tuln | grep 3000`
3. Verifique logs: `cat server_log.txt` e `cat server_error_log.txt`

### Erro de Autenticação

**Problema:** O QR code é exibido, mas o WhatsApp não conecta.

**Solução:**
1. Tente reiniciar a sessão: `./whatsapp_cli.py reset`
2. Verifique se outro dispositivo já está conectado com a mesma conta
3. Limpe os arquivos de sessão: `rm -rf ./server/whatsapp-session`

### Falha no Envio de Mensagens

**Problema:** As mensagens não são entregues.

**Solução:**
1. Verifique o status da conexão: `./whatsapp_cli.py status`
2. Verifique o formato do número: `./whatsapp_cli.py analyze --number NUMERO`
3. Verifique se há tokens suficientes: `./whatsapp_cli.py tokens-status`
4. Verifique os logs: `cat whatsapp_cli.log`

### Problemas com Docker

**Problema:** Os containers Docker não iniciam corretamente.

**Solução:**
1. Verifique os logs: `docker-compose logs`
2. Verifique se as portas estão disponíveis
3. Tente reconstruir os containers: `docker-compose build --no-cache && docker-compose up -d`
