#!/bin/bash
# Script de instalação do WhatsApp Messenger CLI e Admin Panel
# Projetado para ambiente Ubuntu via SSH

set -e

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Função para imprimir mensagens com cores
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_message $GREEN "====================================================="
print_message $GREEN "    WhatsApp Messenger CLI - Script de Instalação    "
print_message $GREEN "====================================================="
echo

# Verifica se está rodando como root
if [ "$EUID" -ne 0 ]; then
    print_message $YELLOW "AVISO: Não está rodando como root. Algumas operações podem falhar."
    read -p "Continuar mesmo assim? (s/n): " choice
    if [[ "$choice" != "s" && "$choice" != "S" ]]; then
        print_message $RED "Instalação cancelada. Execute novamente com sudo."
        exit 1
    fi
fi

# Detecta a versão do Ubuntu
print_message $GREEN "Verificando sistema..."
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VER=$VERSION_ID
    print_message $GREEN "Sistema detectado: $OS $VER"
else
    print_message $YELLOW "Não foi possível determinar a versão do sistema."
    print_message $YELLOW "A instalação pode não funcionar corretamente."
    OS="Unknown"
    VER="Unknown"
fi

# Função para verificar comando
check_command() {
    command -v $1 >/dev/null 2>&1
}

# Verifica e instala dependências do sistema
print_message $GREEN "Verificando e instalando dependências do sistema..."
if ! check_command apt-get; then
    print_message $RED "Comando apt-get não encontrado. Este script requer Ubuntu/Debian."
    exit 1
fi

echo "Atualizando listas de pacotes..."
apt-get update -qq

# Pacotes necessários
PACKAGES="curl wget git python3 python3-pip python3-venv nodejs npm build-essential"

for pkg in $PACKAGES; do
    if ! dpkg -l | grep -q $pkg; then
        print_message $YELLOW "Instalando $pkg..."
        apt-get install -y $pkg
    else
        echo "$pkg já está instalado."
    fi
done

# Verifica Node.js
if ! check_command node || ! check_command npm; then
    print_message $YELLOW "Instalando Node.js e npm..."
    curl -fsSL https://deb.nodesource.com/setup_16.x | bash -
    apt-get install -y nodejs
fi

# Verifica versões
print_message $GREEN "Verificando versões instaladas:"
echo "Python: $(python3 --version)"
echo "Node.js: $(node --version)"
echo "npm: $(npm --version)"

# Cria diretório do projeto
print_message $GREEN "Configurando diretórios do projeto..."
PROJECT_DIR="/opt/whatsapp-messenger"

if [ ! -d "$PROJECT_DIR" ]; then
    mkdir -p $PROJECT_DIR
fi

# Pergunta se deve clonar do Git ou usar arquivos locais
print_message $GREEN "Como deseja instalar o WhatsApp Messenger?"
echo "1) Clonar do repositório Git"
echo "2) Usar arquivos locais (neste diretório)"
read -p "Opção (1/2): " install_option

case $install_option in
    1)
        # Pergunta URL do repositório
        read -p "URL do repositório Git: " git_url
        
        if [ -z "$git_url" ]; then
            print_message $RED "URL do repositório não fornecida. Abortando."
            exit 1
        fi
        
        print_message $GREEN "Clonando repositório..."
        git clone $git_url $PROJECT_DIR/temp
        
        # Move arquivos para o diretório principal
        if [ -d "$PROJECT_DIR/temp" ]; then
            cp -r $PROJECT_DIR/temp/* $PROJECT_DIR/
            rm -rf $PROJECT_DIR/temp
        else
            print_message $RED "Falha ao clonar repositório."
            exit 1
        fi
        ;;
    2)
        print_message $GREEN "Copiando arquivos locais..."
        cp -r ./* $PROJECT_DIR/
        ;;
    *)
        print_message $RED "Opção inválida. Abortando."
        exit 1
        ;;
esac

# Entra no diretório do projeto
cd $PROJECT_DIR

# Configura ambiente virtual Python
print_message $GREEN "Configurando ambiente virtual Python..."
python3 -m venv venv
source venv/bin/activate

# Instala dependências Python
print_message $GREEN "Instalando dependências Python..."
pip install --upgrade pip
pip install -r requirements.txt

# Instala dependências Node.js
print_message $GREEN "Instalando dependências Node.js..."
cd server
npm install
cd ..

# Configurando permissões
print_message $GREEN "Configurando permissões..."
chmod +x whatsapp_cli.py
chmod +x admin_panel.py

# Cria links simbólicos para os comandos
print_message $GREEN "Criando links simbólicos..."
ln -sf $PROJECT_DIR/whatsapp_cli.py /usr/local/bin/whatsapp-cli
ln -sf $PROJECT_DIR/admin_panel.py /usr/local/bin/whatsapp-admin

# Cria serviço systemd para o painel admin
print_message $GREEN "Configurando serviço systemd para o painel administrativo..."
cat > /etc/systemd/system/whatsapp-admin.service << EOL
[Unit]
Description=WhatsApp Messenger Admin Panel
After=network.target

[Service]
Type=simple
User=$(logname)
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/venv/bin/python $PROJECT_DIR/admin_panel.py --host 0.0.0.0 --port 8080
Restart=on-failure
RestartSec=5
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=whatsapp-admin

[Install]
WantedBy=multi-user.target
EOL

# Recarrega configurações do systemd
systemctl daemon-reload

# Pergunta se deseja iniciar o serviço automaticamente
read -p "Deseja iniciar o painel administrativo automaticamente na inicialização? (s/n): " start_service
if [[ "$start_service" == "s" || "$start_service" == "S" ]]; then
    systemctl enable whatsapp-admin
    print_message $GREEN "Serviço configurado para iniciar automaticamente."
else
    print_message $YELLOW "Serviço não será iniciado automaticamente."
fi

# Pergunta se deseja iniciar o serviço agora
read -p "Deseja iniciar o painel administrativo agora? (s/n): " start_now
if [[ "$start_now" == "s" || "$start_now" == "S" ]]; then
    systemctl start whatsapp-admin
    print_message $GREEN "Serviço iniciado."
else
    print_message $YELLOW "Serviço não iniciado. Para iniciar manualmente, execute: sudo systemctl start whatsapp-admin"
fi

# Configura firewall se estiver ativo
if check_command ufw && ufw status | grep -q "Status: active"; then
    print_message $GREEN "Configurando firewall..."
    ufw allow 8080/tcp comment "WhatsApp Admin Panel"
    ufw allow 3000/tcp comment "WhatsApp API"
    print_message $GREEN "Portas 8080 e 3000 abertas no firewall."
fi

# Instruções finais
print_message $GREEN "======================================================"
print_message $GREEN "       Instalação Concluída com Sucesso!               "
print_message $GREEN "======================================================"
echo
print_message $YELLOW "O WhatsApp Messenger CLI e o Painel Admin foram instalados."
echo
echo "Para usar o CLI:"
echo "  whatsapp-cli [comando]"
echo "  Ex: whatsapp-cli status"
echo
echo "Para acessar o Painel Admin:"
echo "  http://$(hostname -I | awk '{print $1}'):8080"
echo
echo "Credenciais padrão do Painel Admin:"
echo "  Usuário: admin"
echo "  Senha: admin123"
echo
print_message $RED "IMPORTANTE: Altere a senha padrão após o primeiro login!"
echo
print_message $GREEN "Para gerenciar o serviço do Painel Admin:"
echo "  sudo systemctl start whatsapp-admin    # Iniciar"
echo "  sudo systemctl stop whatsapp-admin     # Parar"
echo "  sudo systemctl restart whatsapp-admin  # Reiniciar"
echo "  sudo systemctl status whatsapp-admin   # Verificar status"
echo
print_message $GREEN "Logs do Painel Admin:"
echo "  sudo journalctl -u whatsapp-admin -f"
echo
print_message $YELLOW "Desfrute do seu novo WhatsApp Messenger!"
echo
