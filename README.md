# WhatsApp Messenger

Uma solução simples e eficiente para envio de mensagens em massa via WhatsApp, com suporte para arquivos e listas de contatos.

![Versão](https://img.shields.io/badge/Versão-1.0.0-blue)
![Licença](https://img.shields.io/badge/Licença-MIT-green)

## 📋 Visão Geral

WhatsApp Messenger é uma ferramenta que permite enviar mensagens em massa para contatos do WhatsApp utilizando uma interface gráfica amigável. Ideal para marketing, comunicados, lembretes e qualquer situação onde seja necessário enviar a mesma mensagem para múltiplos contatos.

### ✨ Funcionalidades

- ✅ Importação de contatos via CSV ou XLSX
- ✅ Envio de mensagens de texto
- ✅ Suporte para múltiplos anexos
- ✅ Configuração de intervalo entre mensagens
- ✅ Tentativas automáticas em caso de falha
- ✅ Barra de progresso e estimativa de tempo
- ✅ Log detalhado das operações
- ✅ Análise e formatação automática de números de telefone

## 🔧 Requisitos do Sistema

### Para o Servidor (Node.js):
- Node.js v14.0 ou superior
- npm (geralmente vem com o Node.js)

### Para o Cliente (Python):
- Python 3.7 ou superior
- pip (gerenciador de pacotes do Python)

## 🚀 Instalação

Para instruções detalhadas de instalação, consulte o arquivo `setup-guide.md`.

### Resumo rápido:

```bash
# 1. Clone o repositório
git clone <seu-repositorio>
cd whatsapp-messenger

# 2. Configure o Servidor
cd server
npm install

# 3. Configure o Cliente
cd ../client
pip install -r ../python-requirements.txt
```

## 📱 Como Usar

### 1. Inicie o Servidor
```bash
cd server
node server.js
```
O servidor exibirá a mensagem: "Servidor rodando em http://localhost:3000"

### 2. Inicie o Cliente
Em um novo terminal:
```bash
cd client
python whatsapp_messenger.py  # Use python3 no Mac
```

### 3. Autenticação
1. Na interface gráfica, clique em "Verificar Conexão"
2. Se necessário, clique em "Obter QR Code"
3. Escaneie o QR code com seu WhatsApp (como no WhatsApp Web)
4. Aguarde o status mudar para "Conectado e Pronto"

### 4. Envio de Mensagens
1. Clique em "Selecionar" para carregar um arquivo CSV/XLSX com números de telefone
2. Digite sua mensagem na caixa de texto
3. Adicione arquivos para anexar (opcional)
4. Ajuste as configurações de envio conforme necessário
5. Clique em "Iniciar Envio"

## 📂 Estrutura do Projeto

```
whatsapp-messenger/
├── server/               # Servidor Node.js
│   ├── server.js         # Código principal do servidor
│   └── package.json      # Dependências do Node.js
│
├── client/               # Cliente Python
│   └── whatsapp_messenger.py  # Interface gráfica
│
├── python-requirements.txt    # Dependências Python
├── .gitignore            # Arquivos ignorados pelo Git
├── README.md             # Este arquivo
└── setup-guide.md        # Guia detalhado de instalação
```

## 📋 Formato dos Arquivos de Contatos

Os arquivos CSV ou XLSX devem ter:
- Números de telefone na primeira coluna
- Formato recomendado: com código do país (ex: 5511999998888)
- Um número por linha, sem cabeçalho necessário

Exemplo:
```
5511999998888
5511888887777
5521777776666
```

O sistema inclui formatação automática de números e pode adicionar o código do país (55 para Brasil) quando não fornecido.

## ⚠️ Uso Responsável

Este aplicativo deve ser usado de forma responsável e ética:

- **Não use** para enviar spam ou conteúdo indesejado
- **Não abuse** da frequência de envio para evitar bloqueios do WhatsApp
- **Obtenha consentimento** antes de enviar mensagens em massa
- **Respeite** os Termos de Serviço do WhatsApp

## 🔍 Solução de Problemas

### O servidor não inicia
- Verifique se o Node.js está instalado: `node --version`
- Certifique-se de que todas as dependências foram instaladas: `npm install`
- Verifique se a porta 3000 não está em uso

### A interface gráfica não abre
- Verifique se o Python está instalado: `python --version` ou `python3 --version`
- Certifique-se de que as bibliotecas foram instaladas: `pip install -r python-requirements.txt`
- No Windows, se houver erro com tkinter: `pip install tk`

### Não consegue autenticar
- Reinicie o servidor e tente novamente
- Verifique a conexão com a internet
- Certifique-se de que seu celular tem uma conexão estável

### Falha no envio de mensagens
- Verifique o formato dos números de telefone
- Confirme que o WhatsApp está autenticado
- Consulte o arquivo `log.txt` para detalhes dos erros

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo LICENSE para detalhes.

---

⭐ Desenvolvido para simplificar sua comunicação em massa via WhatsApp.