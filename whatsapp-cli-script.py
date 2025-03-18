#!/usr/bin/env python3
"""
WhatsApp Messenger CLI - Interface de linha de comando para o serviço WhatsApp Messenger.
Permite envio de mensagens, gerenciamento de sessões e administração do serviço via terminal.
"""

import argparse
import sys
import os
import requests
import json
import pandas as pd
import time
import datetime
import subprocess
import signal
import logging
from tabulate import tabulate
from pathlib import Path

# Configurações do logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("whatsapp_cli.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("whatsapp-cli")

# Constantes
DEFAULT_API_URL = "http://localhost:3000/api"
CONFIG_DIR = os.path.expanduser("~/.whatsapp-cli")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
SERVER_PID_FILE = os.path.join(CONFIG_DIR, "server.pid")
QR_IMAGE_PATH = os.path.join(CONFIG_DIR, "qrcode.png")

class WhatsAppCLI:
    """Classe principal CLI para o serviço WhatsApp Messenger."""
    
    def __init__(self):
        self._ensure_config_dir()
        self.config = self._get_config()
        self.api_url = self.config.get('api_url', DEFAULT_API_URL)
        self.token = self.config.get('token', '')
        self.user_id = self.config.get('user_id', '')
    
    def _ensure_config_dir(self):
        """Garante que o diretório de configuração existe."""
        os.makedirs(CONFIG_DIR, exist_ok=True)
    
    def _get_config(self):
        """Carrega configuração do arquivo."""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.error("Arquivo de configuração corrompido. Usando configurações padrão.")
        return {}
    
    def _save_config(self, config):
        """Salva configuração no arquivo."""
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
    
    def _make_request(self, method, endpoint, **kwargs):
        """Faz uma requisição para a API."""
        url = f"{self.api_url}/{endpoint}"
        headers = kwargs.pop('headers', {})
        
        # Adiciona o token de autenticação se disponível
        if self.token:
            headers['Authorization'] = f"Bearer {self.token}"
        
        try:
            response = requests.request(
                method, 
                url, 
                headers=headers, 
                **kwargs
            )
            
            if response.status_code == 401:
                logger.error("Erro de autenticação. Faça login novamente.")
                sys.exit(1)
                
            return response
        except requests.RequestException as e:
            logger.error(f"Erro na requisição: {e}")
            return None
    
    def check_status(self, verbose=True):
        """Verifica o status da conexão WhatsApp."""
        response = self._make_request('GET', 'status')
        
        if not response:
            if verbose:
                print("❌ Servidor não disponível. Verifique se o servidor está rodando.")
            return False
            
        if response.status_code != 200:
            if verbose:
                print(f"❌ Erro ao verificar status: {response.status_code}")
            return False
            
        data = response.json()
        ready = data.get('ready', False)
        
        if verbose:
            if ready:
                print("✅ WhatsApp conectado e pronto para uso")
            elif data.get('qrCode', False):
                print("⚠️ Aguardando autenticação. Use o comando 'login' para scanear o QR code.")
            else:
                print("⚠️ Servidor iniciado mas aguardando geração de QR code.")
        
        return ready
    
    def login(self):
        """Gera e exibe o QR code para autenticação."""
        import qrcode
        from PIL import Image
        
        print("Requisitando QR code para autenticação...")
        response = self._make_request('GET', 'qrcode')
        
        if not response:
            print("❌ Não foi possível conectar ao servidor.")
            return
            
        if response.status_code == 202:
            print("⏳ Servidor reiniciando sessão. Aguarde 5 segundos e tente novamente.")
            return
            
        if response.status_code != 200:
            print(f"❌ Erro ao obter QR code: {response.status_code}")
            return
            
        data = response.json()
        qr_text = data.get('qrCodeText')
        
        if not qr_text:
            print("❌ QR code não disponível. Tente reiniciar a sessão com 'reset'.")
            return
            
        # Salva e exibe o QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_text)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(QR_IMAGE_PATH)
        
        print(f"QR code salvo em: {QR_IMAGE_PATH}")
        
        # Tenta abrir o QR code automaticamente
        try:
            if sys.platform == "linux":
                subprocess.call(["xdg-open", QR_IMAGE_PATH])
            elif sys.platform == "darwin":  # macOS
                subprocess.call(["open", QR_IMAGE_PATH])
            elif sys.platform == "win32":
                os.startfile(QR_IMAGE_PATH)
        except:
            # Falha silenciosa se não conseguir abrir
            pass
            
        print("⚠️ Escaneie o QR code com seu WhatsApp para autenticar.")
        print("⏳ Aguardando autenticação...")
        
        # Aguarda até que o cliente esteja pronto
        for i in range(30):  # Tenta por 30 segundos
            time.sleep(1)
            if self.check_status(verbose=False):
                print("✅ WhatsApp conectado com sucesso!")
                return
        
        print("⚠️ Tempo limite excedido. Verifique o status com 'status'.")
    
    def send_text(self, number, message):
        """Envia uma mensagem de texto para um número."""
        if not self.check_status(verbose=False):
            print("❌ WhatsApp não está conectado. Use 'login' para conectar.")
            return
            
        print(f"Enviando mensagem para {number}...")
        response = self._make_request(
            'POST', 
            'send-message',
            json={"number": number, "message": message}
        )
        
        if not response:
            print("❌ Falha ao enviar mensagem.")
            return
            
        if response.status_code != 200:
            error = response.json().get('error', 'Erro desconhecido')
            print(f"❌ Falha ao enviar mensagem: {error}")
            return
            
        data = response.json()
        print(f"✅ Mensagem enviada com sucesso! ID: {data.get('messageId', 'N/A')}")
    
    def send_file(self, number, file_path, caption=""):
        """Envia um arquivo para um número."""
        if not self.check_status(verbose=False):
            print("❌ WhatsApp não está conectado. Use 'login' para conectar.")
            return
            
        if not os.path.exists(file_path):
            print(f"❌ Arquivo não encontrado: {file_path}")
            return
            
        print(f"Enviando arquivo para {number}...")
        
        with open(file_path, 'rb') as f:
            filename = os.path.basename(file_path)
            files = {'file': (filename, f)}
            data = {'number': number}
            
            if caption:
                data['caption'] = caption
                
            response = self._make_request(
                'POST', 
                'send-file',
                data=data,
                files=files
            )
        
        if not response:
            print("❌ Falha ao enviar arquivo.")
            return
            
        if response.status_code != 200:
            error = response.json().get('error', 'Erro desconhecido')
            print(f"❌ Falha ao enviar arquivo: {error}")
            return
            
        data = response.json()
        print(f"✅ Arquivo enviado com sucesso! ID: {data.get('messageId', 'N/A')}")
    
    def send_batch(self, file_path, message=None, files=None, interval=3, random_delay=True):
        """Envia mensagens em lote a partir de um arquivo CSV/XLSX."""
        if not self.check_status(verbose=False):
            print("❌ WhatsApp não está conectado. Use 'login' para conectar.")
            return
        
        if not os.path.exists(file_path):
            print(f"❌ Arquivo não encontrado: {file_path}")
            return
            
        if not message and not files:
            print("❌ É necessário fornecer uma mensagem ou arquivos para enviar.")
            return
            
        # Carrega os contatos do arquivo
        try:
            if file_path.lower().endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.lower().endswith(('.xls', '.xlsx')):
                df = pd.read_excel(file_path)
            else:
                print("❌ Formato de arquivo não suportado. Use CSV ou XLSX.")
                return
                
            contacts = df.iloc[:, 0].dropna().astype(str).tolist()
            print(f"📋 Carregados {len(contacts)} contatos do arquivo.")
            
        except Exception as e:
            print(f"❌ Erro ao ler arquivo: {str(e)}")
            return
            
        # Verifica se os arquivos existem
        if files:
            for file in files:
                if not os.path.exists(file):
                    print(f"❌ Arquivo não encontrado: {file}")
                    return
        
        # Prepara para o envio
        successful = []
        failed = []
        errors = {}
        
        # Processamento do token (simulado)
        tokens_needed = len(contacts) * (1 + len(files) if files else 0)
        print(f"🪙 Tokens necessários para esta operação: {tokens_needed}")
        print(f"🪙 Simulação: tokens disponíveis suficientes.")
        
        # Inicia o envio em lote
        print(f"📤 Iniciando envio para {len(contacts)} contatos...")
        start_time = time.time()
        
        for i, number in enumerate(contacts, 1):
            print(f"[{i}/{len(contacts)}] Processando {number}...")
            success = True
            
            # Envia mensagem de texto
            if message:
                response = self._make_request(
                    'POST', 
                    'send-message',
                    json={"number": number, "message": message}
                )
                
                if not response or response.status_code != 200:
                    error_msg = "Erro de conexão" if not response else response.json().get('error', 'Erro desconhecido')
                    print(f"  ❌ Falha ao enviar texto: {error_msg}")
                    success = False
                    errors[number] = error_msg
                else:
                    print(f"  ✅ Texto enviado com sucesso")
            
            # Envia arquivos
            if files and success:
                for file_path in files:
                    filename = os.path.basename(file_path)
                    print(f"  📎 Enviando arquivo: {filename}")
                    
                    with open(file_path, 'rb') as f:
                        response = self._make_request(
                            'POST',
                            'send-file',
                            data={'number': number},
                            files={'file': (filename, f)}
                        )
                    
                    if not response or response.status_code != 200:
                        error_msg = "Erro de conexão" if not response else response.json().get('error', 'Erro desconhecido')
                        print(f"  ❌ Falha ao enviar arquivo {filename}: {error_msg}")
                        success = False
                        errors[number] = error_msg
                        break
                    else:
                        print(f"  ✅ Arquivo {filename} enviado com sucesso")
            
            # Registra o resultado
            if success:
                successful.append(number)
            else:
                failed.append(number)
            
            # Calcula estatísticas e tempo estimado
            elapsed = time.time() - start_time
            avg_time = elapsed / i
            remaining = len(contacts) - i
            estimated = avg_time * remaining
            
            print(f"⏱️ Progresso: {i}/{len(contacts)} | Restante: ~{int(estimated/60)}m{int(estimated%60)}s")
            
            # Aguarda antes do próximo envio
            if i < len(contacts):
                delay = interval
                if random_delay:
                    import random
                    delay += random.randint(1, 3)
                print(f"⏳ Aguardando {delay}s antes do próximo envio...")
                time.sleep(delay)
        
        # Estatísticas finais
        total_time = time.time() - start_time
        print("\n📊 Relatório de Envio:")
        print(f"Total de contatos: {len(contacts)}")
        print(f"✅ Enviados com sucesso: {len(successful)}")
        print(f"❌ Falhas: {len(failed)}")
        
        if len(contacts) > 0:
            success_rate = (len(successful) / len(contacts)) * 100
            print(f"📈 Taxa de sucesso: {success_rate:.1f}%")
        
        print(f"⏱️ Tempo total: {int(total_time/60)}m{int(total_time%60)}s")
        
        # Exporta falhas para um arquivo CSV se houver alguma
        if failed:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            failures_file = f"falhas_{timestamp}.csv"
            
            with open(failures_file, 'w') as f:
                f.write("numero,erro\n")
                for number in failed:
                    f.write(f"{number},{errors.get(number, 'Erro desconhecido')}\n")
            
            print(f"📄 Números com falha exportados para: {failures_file}")
    
    def analyze_number(self, number):
        """Analisa o formato de um número de telefone."""
        response = self._make_request(
            'POST',
            'analyze-number',
            json={"number": number}
        )
        
        if not response:
            print("❌ Não foi possível conectar ao servidor.")
            return
            
        if response.status_code != 200:
            print(f"❌ Erro ao analisar número: {response.status_code}")
            return
            
        data = response.json()
        
        print("📱 Análise de Número:")
        print(f"Número original: {data.get('original')}")
        print(f"Número limpo: {data.get('cleaned')}")
        print(f"Número formatado: {data.get('formattedNumber')}")
        
        country_info = data.get('countryInfo', {})
        print(f"País: {country_info.get('country', 'Desconhecido')}")
        print(f"Código do país: {country_info.get('code', 'N/A')}")
        print(f"Formato reconhecido: {'Sim' if country_info.get('isFormatted', False) else 'Não'}")
    
    def batch_analyze(self, file_path):
        """Analisa um lote de números de telefone a partir de um arquivo."""
        if not os.path.exists(file_path):
            print(f"❌ Arquivo não encontrado: {file_path}")
            return
            
        # Carrega os números do arquivo
        try:
            if file_path.lower().endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.lower().endswith(('.xls', '.xlsx')):
                df = pd.read_excel(file_path)
            else:
                print("❌ Formato de arquivo não suportado. Use CSV ou XLSX.")
                return
                
            numbers = df.iloc[:, 0].dropna().astype(str).tolist()
            print(f"📋 Carregados {len(numbers)} números do arquivo.")
            
        except Exception as e:
            print(f"❌ Erro ao ler arquivo: {str(e)}")
            return
        
        # Envia para análise
        response = self._make_request(
            'POST',
            'analyze-batch',
            json={"numbers": numbers}
        )
        
        if not response:
            print("❌ Não foi possível conectar ao servidor.")
            return
            
        if response.status_code != 200:
            print(f"❌ Erro ao analisar números: {response.status_code}")
            return
            
        data = response.json()
        stats = data.get('stats', {})
        results = data.get('results', [])
        
        # Exibe estatísticas
        print("\n📊 Estatísticas:")
        print(f"Total de números: {stats.get('total', 0)}")
        print(f"Números com formato reconhecido: {stats.get('formatted', 0)}")
        
        # Exibe distribuição por país
        print("\n🌎 Distribuição por país:")
        for country, count in stats.get('byCountry', {}).items():
            print(f"- {country}: {count} números")
        
        # Exporta resultados para um arquivo CSV
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"analise_numeros_{timestamp}.csv"
        
        with open(output_file, 'w') as f:
            f.write("numero_original,numero_formatado,pais,codigo_pais\n")
            for result in results:
                country_info = result.get('countryInfo', {})
                f.write(f"{result.get('original', '')},{result.get('formattedNumber', '')},{country_info.get('country', 'Desconhecido')},{country_info.get('code', '')}\n")
        
        print(f"\n📄 Análise completa exportada para: {output_file}")
        
        # Pergunta se deseja usar os números formatados
        while True:
            choice = input("\nDeseja usar os números formatados para envio? (s/n): ").lower()
            if choice in ('s', 'sim', 'y', 'yes'):
                # Exporta números formatados
                formatted_file = f"numeros_formatados_{timestamp}.csv"
                with open(formatted_file, 'w') as f:
                    for result in results:
                        f.write(f"{result.get('formattedNumber', '')}\n")
                print(f"📄 Números formatados exportados para: {formatted_file}")
                break
            elif choice in ('n', 'não', 'nao', 'no'):
                print("Operação cancelada.")
                break
            else:
                print("Opção inválida. Digite 's' para sim ou 'n' para não.")
    
    def start_server(self, port=None):
        """Inicia o servidor WhatsApp."""
        # Verifica se o servidor já está rodando
        if os.path.exists(SERVER_PID_FILE):
            with open(SERVER_PID_FILE, 'r') as f:
                pid = f.read().strip()
            
            try:
                os.kill(int(pid), 0)  # Testa se o processo existe
                print(f"⚠️ Servidor já está rodando (PID: {pid}).")
                return
            except OSError:
                # Processo não existe, remove o arquivo PID
                os.remove(SERVER_PID_FILE)
        
        # Define a porta
        if port:
            port_arg = f"--port={port}"
        else:
            port_arg = ""
        
        # Encontra o caminho para o arquivo server.js
        server_js = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "server", "server.js")
        
        if not os.path.exists(server_js):
            print(f"❌ Arquivo server.js não encontrado em {server_js}")
            return
        
        # Inicia o servidor
        try:
            print("🚀 Iniciando servidor WhatsApp...")
            
            # Direciona saída para arquivos de log
            log_file = open("server_log.txt", "w")
            error_log = open("server_error_log.txt", "w")
            
            # Inicia o processo
            process = subprocess.Popen(
                ["node", server_js, port_arg],
                stdout=log_file,
                stderr=error_log,
                preexec_fn=os.setsid,  # Permite matar o processo e seus filhos
                start_new_session=True
            )
            
            # Salva o PID
            with open(SERVER_PID_FILE, 'w') as f:
                f.write(str(process.pid))
            
            print(f"✅ Servidor iniciado com PID: {process.pid}")
            print(f"📄 Logs: server_log.txt | Erros: server_error_log.txt")
            
            # Aguarda alguns segundos e verifica o status
            time.sleep(5)
            self.check_status()
            
        except Exception as e:
            print(f"❌ Erro ao iniciar servidor: {str(e)}")
    
    def stop_server(self):
        """Para o servidor WhatsApp."""
        if not os.path.exists(SERVER_PID_FILE):
            print("⚠️ Servidor não está rodando.")
            return
            
        try:
            with open(SERVER_PID_FILE, 'r') as f:
                pid = int(f.read().strip())
                
            print(f"🛑 Parando servidor (PID: {pid})...")
            
            # Envia SIGTERM para o grupo de processos
            os.killpg(os.getpgid(pid), signal.SIGTERM)
            
            # Aguarda um momento e verifica se o processo ainda existe
            time.sleep(2)
            try:
                os.kill(pid, 0)
                print("⚠️ Servidor não respondeu ao SIGTERM, forçando parada...")
                os.killpg(os.getpgid(pid), signal.SIGKILL)
            except OSError:
                # Processo já terminou
                pass
                
            # Remove o arquivo PID
            os.remove(SERVER_PID_FILE)
            print("✅ Servidor parado com sucesso.")
            
        except Exception as e:
            print(f"❌ Erro ao parar servidor: {str(e)}")
    
    def reset_session(self):
        """Reinicia a sessão do WhatsApp."""
        print("🔄 Reiniciando sessão do WhatsApp...")
        
        response = self._make_request('POST', 'reset-session')
        
        if not response:
            print("❌ Não foi possível conectar ao servidor.")
            return
            
        if response.status_code != 200:
            error = response.json().get('error', 'Erro desconhecido')
            print(f"❌ Falha ao reiniciar sessão: {error}")
            return
            
        print("✅ Sessão reiniciada com sucesso!")
        print("⚠️ Use o comando 'login' para escanear o novo QR code.")
    
    def tokens_status(self):
        """Verifica o status dos tokens (simulado)."""
        print("🪙 Sistema de Tokens (Simulado)")
        print("Tokens disponíveis: 1000")
        print("Tokens usados este mês: 250")
        print("Validade: 31/12/2025")

def main():
    """Ponto de entrada principal para o CLI."""
    parser = argparse.ArgumentParser(description="WhatsApp Messenger CLI")
    subparsers = parser.add_subparsers(dest="command", help="Comando a executar")
    
    # Comando status
    status_parser = subparsers.add_parser("status", help="Verifica o status da conexão WhatsApp")
    
    # Comando login
    login_parser = subparsers.add_parser("login", help="Gera QR code para autenticação")
    
    # Comando enviar texto
    send_text_parser = subparsers.add_parser("send-text", help="Envia uma mensagem de texto")
    send_text_parser.add_argument("--to", "-t", required=True, help="Número do destinatário")
    send_text_parser.add_argument("--message", "-m", required=True, help="Texto da mensagem")
    
    # Comando enviar arquivo
    send_file_parser = subparsers.add_parser("send-file", help="Envia um arquivo")
    send_file_parser.add_argument("--to", "-t", required=True, help="Número do destinatário")
    send_file_parser.add_argument("--file", "-f", required=True, help="Caminho do arquivo")
    send_file_parser.add_argument("--caption", "-c", help="Legenda do arquivo")
    
    # Comando enviar lote
    send_batch_parser = subparsers.add_parser("send-batch", help="Envia mensagens em lote")
    send_batch_parser.add_argument("--file", "-f", required=True, help="Arquivo CSV/XLSX com contatos")
    send_batch_parser.add_argument("--message", "-m", help="Texto da mensagem")
    send_batch_parser.add_argument("--files", nargs="+", help="Arquivos para anexar")
    send_batch_parser.add_argument("--interval", "-i", type=int, default=3, help="Intervalo entre mensagens (segundos)")
    send_batch_parser.add_argument("--no-random", action="store_false", dest="random_delay", help="Desativa variação aleatória no intervalo")
    
    # Comando analisar número
    analyze_parser = subparsers.add_parser("analyze", help="Analisa formato de número de telefone")
    analyze_parser.add_argument("--number", "-n", required=True, help="Número de telefone para analisar")
    
    # Comando analisar lote
    batch_analyze_parser = subparsers.add_parser("batch-analyze", help="Analisa lote de números de telefone")
    batch_analyze_parser.add_argument("--file", "-f", required=True, help="Arquivo CSV/XLSX com números de telefone")
    
    # Comandos de gerenciamento do servidor
    start_server_parser = subparsers.add_parser("start-server", help="Inicia o servidor WhatsApp")
    start_server_parser.add_argument("--port", "-p", type=int, help="Porta para o servidor")
    
    subparsers.add_parser("stop-server", help="Para o servidor WhatsApp")
    subparsers.add_parser("status-server", help="Verifica o status do servidor")
    
    # Gerenciamento de sessão
    subparsers.add_parser("reset", help="Reinicia a sessão do WhatsApp")
    
    # Gerenciamento de tokens (placeholder para implementação futura)
    subparsers.add_parser("tokens-status", help="Verifica tokens restantes")
    
    args = parser.parse_args()
    cli = WhatsAppCLI()
    
    if args.command == "status":
        cli.check_status()
    elif args.command == "login":
        cli.login()
    elif args.command == "send-text":
        cli.send_text(args.to, args.message)
    elif args.command == "send-file":
        cli.send_file(args.to, args.file, args.caption)
    elif args.command == "send-batch":
        cli.send_batch(args.file, args.message, args.files, args.interval, args.random_delay)
    elif args.command == "analyze":
        cli.analyze_number(args.number)
    elif args.command == "batch-analyze":
        cli.batch_analyze(args.file)
    elif args.command == "start-server":
        cli.start_server(args.port)
    elif args.command == "stop-server":
        cli.stop_server()
    elif args.command == "status-server":
        cli.check_status()
    elif args.command == "reset":
        cli.reset_session()
    elif args.command == "tokens-status":
        cli.tokens_status()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
