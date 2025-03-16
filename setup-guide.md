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

### Para Linux:
1. Instale o Node.js e npm:
   ```
   sudo apt update
   sudo apt install nodejs npm
   ```
2. Instale o Python:
   ```
   sudo apt install python3 python3-pip
   ```

## Preparação da Aplicação

### Opção 1: Clonando do repositório (se estiver usando Git)
```bash
git clone <seu-repositorio>
cd whatsapp-messenger
```

### Opção 2: Download direto
1. Baixe os arquivos do projeto
2. Extraia para uma pasta chamada `whatsapp-messenger`
3. Abra o terminal/prompt de comando nessa pasta

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
   Este comando instalará todas as bibliotecas necessárias listadas no arquivo `package.json`:
   - express
   - whatsapp-web.js
   - cors
   - body-parser
   - multer
   - qrcode-terminal

### Configurando o Cliente Python:
1. Abra um terminal/prompt de comando
2. Navegue até a pasta principal do projeto:
   ```
   cd whatsapp-messenger  # Se já não estiver nela
   ```
3. Instale as dependências necessárias:
   ```
   # No Windows:
   pip install -r python-requirements.txt
   
   # No Mac/Linux:
   pip3 install -r python-requirements.txt
   ```
   
   Este comando instalará:
   - pandas
   - requests
   - pillow
   - ttkbootstrap (para a interface gráfica moderna)

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
   - Se a porta 3000 estiver ocupada, o servidor tentará portas alternativas

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
   
   # No Mac/Linux:
   python3 whatsapp_messenger.py
   ```
4. A interface gráfica será exibida

### Etapa 3: Autentique o WhatsApp
1. Na interface gráfica, clique em "Verificar Conexão"
2. Se o status mostrar "Aguardando Autenticação", clique em "Obter QR Code"
3. Escaneie o QR code com seu WhatsApp no celular (como você faria com o WhatsApp Web)
4. Quando o status mudar para "Conectado e Pronto", você pode começar a usar o sistema

## Utilização
1. Carregue um arquivo CSV/XLSX com números de telefone na primeira coluna:
   - Clique em "Selecionar" para carregar o arquivo
   - O sistema pedirá se deseja analisar os formatos dos números
   - Se aceitar, ele formatará automaticamente os números para o padrão internacional

2. Digite a mensagem que deseja enviar na caixa de texto

3. Opcionalmente, adicione arquivos para anexar:
   - Clique em "Selecionar Arquivos"
   - Você pode incluir imagens, PDFs, documentos, etc.

4. Ajuste as configurações de envio conforme necessário:
   - Intervalo entre mensagens (em segundos)
   - Número de tentativas
   - Variação aleatória no intervalo

5. Clique em "Iniciar Envio"
   - A barra de progresso mostrará o andamento
   - As estatísticas de envio serão atualizadas em tempo real

## Solução de Problemas

### Servidor não inicia:
- Verifique se o Node.js está instalado corretamente: `node --version`
- Certifique-se de que todas as dependências foram instaladas: `npm install`
- Verifique se a porta 3000 não está sendo usada por outro aplicativo (o servidor tentará portas alternativas)
- Verifique os logs para erros específicos

### Cliente não inicia:
- Verifique se o Python está instalado corretamente: `python --version` ou `python3 --version`
- Certifique-se de que todas as bibliotecas Python foram instaladas: `pip list`
- No Windows, se houver erro com tkinter, instale-o separadamente: `pip install tk`

### QR Code não aparece:
- Certifique-se de que o servidor está rodando
- Clique no botão "Obter QR Code" na interface
- Se estiver usando portas alternativas, clique em "Alterar Porta" e tente outras portas
- Reinicie tanto o servidor quanto o cliente

### Erros de envio de mensagem:
- Verifique o formato dos números de telefone (use a análise de números para formatação automática)
- Certifique-se de que o WhatsApp está autenticado
- Consulte os logs recentes na interface ou o arquivo `log.txt` para mensagens de erro específicas

## Manutenção

### Sessão do WhatsApp:
- A sessão do WhatsApp é salva em `server/whatsapp-session/`
- Se precisar reiniciar a sessão, use o botão "Reiniciar Sessão" na interface

### Logs:
- Os logs da aplicação são salvos em `log.txt`
- A interface também mostra logs recentes na seção "Atividade Recente"

### Alteração de porta:
- Se precisar mudar a porta do servidor, clique em "Alterar Porta" na interface
- Você pode selecionar entre várias portas alternativas (3000-3005)