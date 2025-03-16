# Guia de Instalação do WhatsApp Messenger

Este é um guia simplificado para instalar e executar o aplicativo WhatsApp Messenger para envio automatizado de mensagens.

## Requisitos Prévios

### Para Windows:
1. Instale o [Node.js](https://nodejs.org/) (versão 14.0 ou superior)
2. Instale o [Python](https://www.python.org/downloads/) (versão 3.7 ou superior)
3. Certifique-se de marcar a opção "Add Python to PATH" durante a instalação do Python

### Para Mac:
1. Instale o Node.js usando [Homebrew](https://brew.sh/):
   ```
   brew install node
   ```
2. O Python já vem pré-instalado no Mac, mas caso precise atualizar:
   ```
   brew install python
   ```

## Preparação da Aplicação

1. Crie uma nova pasta para o projeto:
   ```
   mkdir whatsapp-messenger
   cd whatsapp-messenger
   ```

2. Crie duas subpastas:
   ```
   mkdir server
   mkdir client
   ```

3. Coloque os arquivos da seguinte forma:
   - Na pasta `server`: `server.js` e `package.json`
   - Na pasta `client`: `whatsapp_messenger.py` (arquivo renomeado do client-fixed-updated.py)

## Instalação

### Configurando o Servidor Node.js:
1. Abra um terminal/prompt de comando
2. Navegue até a pasta `server`:
   ```
   cd server
   ```
3. Instale as dependências:
   ```
   npm install
   ```

### Configurando o Cliente Python:
1. Abra um terminal/prompt de comando
2. Navegue até a pasta `client`:
   ```
   cd client
   ```
3. Instale as dependências necessárias:
   ```
   # No Windows:
   pip install pandas requests pillow tkinter
   
   # No Mac:
   pip3 install pandas requests pillow
   ```

## Executando a Aplicação

### Etapa 1: Inicie o Servidor
1. Abra um terminal/prompt de comando
2. Navegue até a pasta `server`:
   ```
   cd server
   ```
3. Inicie o servidor:
   ```
   node server.js
   ```
4. O servidor exibirá: "Servidor rodando em http://localhost:3000"

### Etapa 2: Inicie o Cliente
1. Abra outro terminal/prompt de comando
2. Navegue até a pasta `client`:
   ```
   cd client
   ```
3. Inicie o cliente:
   ```
   # No Windows:
   python whatsapp_messenger.py
   
   # No Mac:
   python3 whatsapp_messenger.py
   ```
4. A interface gráfica será exibida

### Etapa 3: Autentique o WhatsApp
1. Na interface gráfica, clique em "Verificar Conexão"
2. Se o status mostrar "Aguardando Autenticação", clique em "Obter QR Code"
3. Escaneie o QR code com seu WhatsApp no celular (como você faria com o WhatsApp Web)
4. Quando o status mudar para "Conectado e Pronto", você pode começar a usar o sistema

## Utilização
1. Carregue um arquivo CSV/XLSX com números de telefone na primeira coluna
2. Digite a mensagem que deseja enviar
3. Opcionalmente, adicione arquivos para anexar
4. Ajuste as configurações de envio conforme necessário
5. Clique em "Iniciar Envio"

## Solução de Problemas

### Servidor não inicia:
- Verifique se o Node.js está instalado corretamente: `node --version`
- Certifique-se de que todas as dependências foram instaladas: `npm install`
- Verifique se a porta 3000 não está sendo usada por outro aplicativo

### Cliente não inicia:
- Verifique se o Python está instalado corretamente: `python --version` ou `python3 --version`
- Certifique-se de que todas as bibliotecas Python foram instaladas
- No Windows, se houver erro com tkinter, instale-o separadamente: `pip install tk`

### QR Code não aparece:
- Certifique-se de que o servidor está rodando
- Verifique a conexão entre o cliente e o servidor (localhost:3000)
- Reinicie tanto o servidor quanto o cliente

### Erros de envio de mensagem:
- Verifique o formato dos números de telefone (use formato internacional: +55XXYYYYYYYY)
- Certifique-se de que o WhatsApp está autenticado
- Verifique os logs para mensagens de erro específicas
