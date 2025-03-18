#!/usr/bin/env python3
"""
Painel Administrativo para WhatsApp Messenger
Fornece uma interface web básica para gerenciar o serviço via SSH
"""

import os
import sys
import json
import time
import datetime
import subprocess
import logging
import requests
import psutil
import threading
from functools import wraps
from flask import Flask, request, render_template, jsonify, redirect, url_for, session, flash, send_file
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("admin_panel.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("admin-panel")

# Constantes e configurações
DEFAULT_API_URL = "http://localhost:3000/api"
CONFIG_DIR = os.path.expanduser("~/.whatsapp-cli")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
SERVER_PID_FILE = os.path.join(CONFIG_DIR, "server.pid")
ADMIN_USERS_FILE = os.path.join(CONFIG_DIR, "admin_users.json")
QR_IMAGE_PATH = os.path.join(CONFIG_DIR, "qrcode.png")
SECRET_KEY = os.environ.get("SECRET_KEY", "whatsapp-admin-secret-key-change-in-production")

# Garantir diretórios existam
os.makedirs(CONFIG_DIR, exist_ok=True)

# Criar arquivo de usuários admin se não existir
if not os.path.exists(ADMIN_USERS_FILE):
    with open(ADMIN_USERS_FILE, 'w') as f:
        json.dump({
            "users": [
                {
                    "username": "admin",
                    "password": generate_password_hash("admin123"),  # Senha padrão, mudar após primeiro login!
                    "role": "admin",
                    "created": datetime.datetime.now().isoformat()
                }
            ]
        }, f, indent=2)
    logger.warning("Arquivo de usuários admin criado com credenciais padrão. Altere após o primeiro login!")

# Inicializar Flask
app = Flask(__name__, 
    template_folder=os.path.join(os.path.dirname(__file__), "templates"),
    static_folder=os.path.join(os.path.dirname(__file__), "static")
)
app.secret_key = SECRET_KEY
CORS(app)

# Status e métricas
server_status = {
    "running": False,
    "pid": None,
    "uptime": 0,
    "start_time": None,
    "whatsapp_connected": False,
    "messages_sent_session": 0,
    "files_sent_session": 0,
    "errors_session": 0
}

# Cache do QR code
qr_code_data = None
last_qr_update = None

# Funções utilitárias
def load_config():
    """Carrega configuração do arquivo."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error("Arquivo de configuração corrompido.")
    return {}

def save_config(config):
    """Salva configuração no arquivo."""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def load_admin_users():
    """Carrega usuários administrativos."""
    if os.path.exists(ADMIN_USERS_FILE):
        try:
            with open(ADMIN_USERS_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error("Arquivo de usuários corrompido.")
    return {"users": []}

def save_admin_users(users_data):
    """Salva usuários administrativos."""
    with open(ADMIN_USERS_FILE, 'w') as f:
        json.dump(users_data, f, indent=2)

def update_server_status():
    """Atualiza o status do servidor."""
    global server_status
    
    # Verifica se o servidor está rodando
    if os.path.exists(SERVER_PID_FILE):
        try:
            with open(SERVER_PID_FILE, 'r') as f:
                pid = int(f.read().strip())
                
            if psutil.pid_exists(pid):
                process = psutil.Process(pid)
                server_status["running"] = True
                server_status["pid"] = pid
                server_status["start_time"] = process.create_time()
                server_status["uptime"] = time.time() - process.create_time()
                
                # Tenta verificar status da conexão WhatsApp
                try:
                    config = load_config()
                    api_url = config.get('api_url', DEFAULT_API_URL)
                    response = requests.get(f"{api_url}/status", timeout=2)
                    if response.status_code == 200:
                        data = response.json()
                        server_status["whatsapp_connected"] = data.get('ready', False)
                    else:
                        server_status["whatsapp_connected"] = False
                except:
                    server_status["whatsapp_connected"] = False
                
                return
        except (ValueError, IOError, psutil.NoSuchProcess) as e:
            logger.error(f"Erro ao verificar processo: {e}")
    
    # Se chegou aqui, o servidor não está rodando
    server_status["running"] = False
    server_status["pid"] = None
    server_status["start_time"] = None
    server_status["uptime"] = 0
    server_status["whatsapp_connected"] = False

def get_system_stats():
    """Obtém estatísticas do sistema."""
    stats = {
        "cpu_percent": psutil.cpu_percent(interval=0.5),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent,
        "network": {
            "sent": psutil.net_io_counters().bytes_sent,
            "recv": psutil.net_io_counters().bytes_recv
        },
        "timestamp": datetime.datetime.now().isoformat()
    }
    return stats

def get_whatsapp_qr():
    """Obtém o QR code do WhatsApp se disponível."""
    global qr_code_data, last_qr_update
    
    # Se temos um QR code recente (menos de 30 segundos), retorna o cache
    if qr_code_data and last_qr_update and (time.time() - last_qr_update) < 30:
        return qr_code_data
    
    config = load_config()
    api_url = config.get('api_url', DEFAULT_API_URL)
    
    try:
        response = requests.get(f"{api_url}/qrcode", timeout=5)
        if response.status_code == 200:
            data = response.json()
            qr_text = data.get('qrCodeText')
            
            if qr_text:
                import qrcode
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
                
                qr_code_data = {"available": True, "path": QR_IMAGE_PATH}
                last_qr_update = time.time()
                return qr_code_data
    except Exception as e:
        logger.error(f"Erro ao obter QR code: {e}")
    
    return {"available": False}

def execute_cli_command(command, args=None):
    """Executa um comando no CLI."""
    cli_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "whatsapp_cli.py")
    
    if not os.path.exists(cli_path):
        return {"success": False, "error": f"CLI não encontrado em {cli_path}"}
    
    cmd = [sys.executable, cli_path, command]
    if args:
        for k, v in args.items():
            if v is True:
                cmd.append(f"--{k}")
            elif v is not False and v is not None:
                cmd.append(f"--{k}")
                cmd.append(str(v))
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr,
            "code": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Comando expirou (timeout)"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Decorador para verificar login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash("Faça login para acessar esta página", "warning")
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Decorador para verificar permissão de administrador
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash("Faça login para acessar esta página", "warning")
            return redirect(url_for('login', next=request.url))
        if session.get('role') != 'admin':
            flash("Permissão negada. Acesso de administrador necessário.", "danger")
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Rotas da aplicação
@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin_users = load_admin_users()
        user = next((u for u in admin_users.get('users', []) if u['username'] == username), None)
        
        if user and check_password_hash(user['password'], password):
            session['user'] = username
            session['role'] = user.get('role', 'user')
            flash(f"Bem-vindo, {username}!", "success")
            return redirect(url_for('dashboard'))
        
        flash("Credenciais inválidas. Tente novamente.", "danger")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Você foi desconectado.", "info")
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    update_server_status()
    system_stats = get_system_stats()
    
    # Obtém QR code se o servidor estiver rodando mas WhatsApp não conectado
    qr_info = {"available": False}
    if server_status["running"] and not server_status["whatsapp_connected"]:
        qr_info = get_whatsapp_qr()
    
    return render_template(
        'dashboard.html',
        server_status=server_status,
        system_stats=system_stats,
        qr_info=qr_info,
        username=session.get('user'),
        role=session.get('role')
    )

@app.route('/api/server/start', methods=['POST'])
@login_required
def api_start_server():
    port = request.json.get('port', None)
    result = execute_cli_command('start-server', {'port': port} if port else None)
    update_server_status()
    return jsonify(result)

@app.route('/api/server/stop', methods=['POST'])
@login_required
def api_stop_server():
    result = execute_cli_command('stop-server')
    update_server_status()
    return jsonify(result)

@app.route('/api/server/status', methods=['GET'])
@login_required
def api_server_status():
    update_server_status()
    return jsonify(server_status)

@app.route('/api/system/stats', methods=['GET'])
@login_required
def api_system_stats():
    return jsonify(get_system_stats())

@app.route('/api/whatsapp/login', methods=['POST'])
@login_required
def api_whatsapp_login():
    result = execute_cli_command('login')
    return jsonify(result)

@app.route('/api/whatsapp/reset', methods=['POST'])
@login_required
def api_whatsapp_reset():
    result = execute_cli_command('reset')
    return jsonify(result)

@app.route('/api/whatsapp/qrcode', methods=['GET'])
@login_required
def api_whatsapp_qrcode():
    qr_info = get_whatsapp_qr()
    if qr_info.get('available') and qr_info.get('path'):
        return send_file(qr_info['path'], mimetype='image/png')
    return jsonify({"error": "QR code não disponível"}), 404

@app.route('/api/message/send-text', methods=['POST'])
@login_required
def api_send_text():
    number = request.json.get('number')
    message = request.json.get('message')
    
    if not number or not message:
        return jsonify({"success": False, "error": "Número e mensagem são obrigatórios"})
    
    result = execute_cli_command('send-text', {'to': number, 'message': message})
    
    if result.get('success'):
        server_status["messages_sent_session"] += 1
    else:
        server_status["errors_session"] += 1
    
    return jsonify(result)

@app.route('/api/message/send-file', methods=['POST'])
@login_required
def api_send_file():
    number = request.form.get('number')
    caption = request.form.get('caption', '')
    
    if not number or 'file' not in request.files:
        return jsonify({"success": False, "error": "Número e arquivo são obrigatórios"})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "Nenhum arquivo selecionado"})
    
    # Salva arquivo temporariamente
    temp_path = os.path.join('/tmp', file.filename)
    file.save(temp_path)
    
    result = execute_cli_command('send-file', {
        'to': number, 
        'file': temp_path,
        'caption': caption
    })
    
    # Remove arquivo temporário
    try:
        os.remove(temp_path)
    except:
        pass
    
    if result.get('success'):
        server_status["files_sent_session"] += 1
    else:
        server_status["errors_session"] += 1
    
    return jsonify(result)

@app.route('/api/message/send-batch', methods=['POST'])
@login_required
def api_send_batch():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "Arquivo de contatos é obrigatório"})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "Nenhum arquivo selecionado"})
    
    message = request.form.get('message', '')
    interval = request.form.get('interval', '3')
    random_delay = 'no_random' not in request.form
    
    # Salva arquivo temporariamente
    temp_path = os.path.join('/tmp', file.filename)
    file.save(temp_path)
    
    # Se tem arquivos para anexar
    attachment_files = []
    if 'attachments[]' in request.files:
        for attachment in request.files.getlist('attachments[]'):
            attach_path = os.path.join('/tmp', attachment.filename)
            attachment.save(attach_path)
            attachment_files.append(attach_path)
    
    # Inicia em thread separada para não bloquear a resposta
    def run_batch_job():
        args = {
            'file': temp_path,
            'message': message,
            'interval': interval
        }
        
        if not random_delay:
            args['no_random'] = True
            
        if attachment_files:
            args['files'] = ' '.join(attachment_files)
        
        # Executa o comando
        result = execute_cli_command('send-batch', args)
        
        # Atualiza contadores
        if result.get('success'):
            # Tenta estimar o número enviado
            try:
                output = result.get('output', '')
                sent_count = 0
                for line in output.splitlines():
                    if "Mensagem enviada com sucesso" in line:
                        sent_count += 1
                server_status["messages_sent_session"] += sent_count
            except:
                pass
        else:
            server_status["errors_session"] += 1
        
        # Limpa arquivos temporários
        try:
            os.remove(temp_path)
            for attach_path in attachment_files:
                os.remove(attach_path)
        except:
            pass
    
    # Inicia thread
    thread = threading.Thread(target=run_batch_job)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        "success": True, 
        "message": "Processamento iniciado em segundo plano."
    })

@app.route('/api/tokens/status', methods=['GET'])
@login_required
def api_tokens_status():
    result = execute_cli_command('tokens-status')
    return jsonify(result)

@app.route('/users')
@admin_required
def users():
    admin_users = load_admin_users()
    return render_template('users.html', users=admin_users.get('users', []))

@app.route('/api/users/add', methods=['POST'])
@admin_required
def api_add_user():
    username = request.json.get('username')
    password = request.json.get('password')
    role = request.json.get('role', 'user')
    
    if not username or not password:
        return jsonify({"success": False, "error": "Nome de usuário e senha são obrigatórios"})
    
    admin_users = load_admin_users()
    
    # Verifica se usuário já existe
    if any(u['username'] == username for u in admin_users.get('users', [])):
        return jsonify({"success": False, "error": "Nome de usuário já existe"})
    
    # Cria novo usuário
    new_user = {
        "username": username,
        "password": generate_password_hash(password),
        "role": role,
        "created": datetime.datetime.now().isoformat()
    }
    
    admin_users['users'].append(new_user)
    save_admin_users(admin_users)
    
    return jsonify({"success": True})

@app.route('/api/users/delete', methods=['POST'])
@admin_required
def api_delete_user():
    username = request.json.get('username')
    
    if not username:
        return jsonify({"success": False, "error": "Nome de usuário é obrigatório"})
    
    # Não pode deletar a si mesmo
    if username == session.get('user'):
        return jsonify({"success": False, "error": "Não é possível excluir seu próprio usuário"})
    
    admin_users = load_admin_users()
    
    # Remove o usuário
    admin_users['users'] = [u for u in admin_users.get('users', []) if u['username'] != username]
    save_admin_users(admin_users)
    
    return jsonify({"success": True})

@app.route('/api/users/change-password', methods=['POST'])
@login_required
def api_change_password():
    username = session.get('user')
    old_password = request.json.get('old_password')
    new_password = request.json.get('new_password')
    
    if not old_password or not new_password:
        return jsonify({"success": False, "error": "Ambas as senhas são obrigatórias"})
    
    admin_users = load_admin_users()
    user = next((u for u in admin_users.get('users', []) if u['username'] == username), None)
    
    if not user or not check_password_hash(user['password'], old_password):
        return jsonify({"success": False, "error": "Senha atual incorreta"})
    
    # Atualiza senha
    for u in admin_users['users']:
        if u['username'] == username:
            u['password'] = generate_password_hash(new_password)
            break
    
    save_admin_users(admin_users)
    
    return jsonify({"success": True})

@app.route('/logs')
@login_required
def logs():
    log_files = [
        {"name": "Admin Panel", "path": "admin_panel.log"},
        {"name": "CLI", "path": "whatsapp_cli.log"},
        {"name": "Servidor", "path": "server_log.txt"},
        {"name": "Erros do Servidor", "path": "server_error_log.txt"}
    ]
    
    selected_log = request.args.get('file', 'admin_panel.log')
    log_content = "Log não encontrado"
    
    # Validar o nome do arquivo para evitar directory traversal
    if os.path.basename(selected_log) == selected_log and os.path.exists(selected_log):
        try:
            with open(selected_log, 'r') as f:
                # Pegando as últimas 500 linhas para evitar arquivos muito grandes
                log_content = ''.join(f.readlines()[-500:])
        except Exception as e:
            log_content = f"Erro ao ler arquivo: {str(e)}"
    
    return render_template('logs.html', log_files=log_files, selected_log=selected_log, log_content=log_content)

@app.route('/backup', methods=['GET', 'POST'])
@admin_required
def backup():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'create_backup':
            # Criar backup
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = os.path.join(CONFIG_DIR, 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            
            backup_path = os.path.join(backup_dir, f'whatsapp_backup_{timestamp}.zip')
            
            try:
                import shutil
                # Diretórios a serem incluídos no backup
                dirs_to_backup = [
                    CONFIG_DIR,
                    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "server", "whatsapp-session")
                ]
                
                # Criar arquivo ZIP
                shutil.make_archive(
                    backup_path.replace('.zip', ''),
                    'zip',
                    root_dir='/',
                    base_dir=None,
                    verbose=True
                )
                
                flash(f"Backup criado com sucesso: {backup_path}", "success")
            except Exception as e:
                flash(f"Erro ao criar backup: {str(e)}", "danger")
        
        elif action == 'restore_backup':
            # Restaurar backup
            backup_file = request.files.get('backup_file')
            if not backup_file:
                flash("Nenhum arquivo de backup selecionado", "warning")
            else:
                try:
                    import zipfile
                    temp_path = os.path.join('/tmp', 'whatsapp_restore.zip')
                    backup_file.save(temp_path)
                    
                    # Extrair ZIP
                    with zipfile.ZipFile(temp_path, 'r') as zip_ref:
                        zip_ref.extractall('/')
                    
                    os.remove(temp_path)
                    flash("Backup restaurado com sucesso. Reinicie os serviços.", "success")
                except Exception as e:
                    flash(f"Erro ao restaurar backup: {str(e)}", "danger")
    
    # Listar backups existentes
    backups = []
    backup_dir = os.path.join(CONFIG_DIR, 'backups')
    if os.path.exists(backup_dir):
        backups = [f for f in os.listdir(backup_dir) if f.startswith('whatsapp_backup_') and f.endswith('.zip')]
        backups.sort(reverse=True)
    
    return render_template('backup.html', backups=backups)

@app.route('/download_backup/<filename>')
@admin_required
def download_backup(filename):
    backup_dir = os.path.join(CONFIG_DIR, 'backups')
    return send_file(os.path.join(backup_dir, filename), as_attachment=True)

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    config = load_config()
    
    if request.method == 'POST':
        config['api_url'] = request.form.get('api_url', DEFAULT_API_URL)
        
        # Outras configurações
        save_config(config)
        flash("Configurações salvas com sucesso!", "success")
    
    return render_template('settings.html', config=config)

@app.route('/analyze')
@login_required
def analyze():
    return render_template('analyze.html')

@app.route('/api/analyze/number', methods=['POST'])
@login_required
def api_analyze_number():
    number = request.json.get('number')
    
    if not number:
        return jsonify({"success": False, "error": "Número é obrigatório"})
    
    result = execute_cli_command('analyze', {'number': number})
    return jsonify(result)

@app.route('/api/analyze/batch', methods=['POST'])
@login_required
def api_analyze_batch():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "Arquivo é obrigatório"})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "Nenhum arquivo selecionado"})
    
    # Salva arquivo temporariamente
    temp_path = os.path.join('/tmp', file.filename)
    file.save(temp_path)
    
    result = execute_cli_command('batch-analyze', {'file': temp_path})
    
    # Remove arquivo temporário
    try:
        os.remove(temp_path)
    except:
        pass
    
    return jsonify(result)

# Principal
def create_template_dirs():
    """Cria os diretórios de templates e arquivos estáticos se não existirem."""
    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    
    os.makedirs(template_dir, exist_ok=True)
    os.makedirs(static_dir, exist_ok=True)
    os.makedirs(os.path.join(static_dir, "css"), exist_ok=True)
    os.makedirs(os.path.join(static_dir, "js"), exist_ok=True)
    
    # Cria um HTML básico de login se não existir
    login_template = os.path.join(template_dir, "login.html")
    if not os.path.exists(login_template):
        with open(login_template, 'w') as f:
            f.write("""<!DOCTYPE html>
<html>
<head>
    <title>Login - WhatsApp Messenger Admin</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background-color: #f5f5f5;
            height: 100vh;
            display: flex;
            align-items: center;
            padding-top: 40px;
            padding-bottom: 40px;
        }
        .form-signin {
            max-width: 330px;
            padding: 15px;
        }
        .form-signin .form-floating:focus-within {
            z-index: 2;
        }
        .form-signin input[type="text"] {
            margin-bottom: -1px;
            border-bottom-right-radius: 0;
            border-bottom-left-radius: 0;
        }
        .form-signin input[type="password"] {
            margin-bottom: 10px;
            border-top-left-radius: 0;
            border-top-right-radius: 0;
        }
    </style>
</head>
<body class="text-center">
    <main class="form-signin w-100 m-auto">
        <form method="post">
            <img class="mb-4" src="https://via.placeholder.com/72x72?text=W" alt="Logo" width="72" height="72">
            <h1 class="h3 mb-3 fw-normal">WhatsApp Messenger Admin</h1>
            
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ category }}">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <div class="form-floating">
                <input type="text" class="form-control" id="username" name="username" placeholder="Nome de usuário" required>
                <label for="username">Nome de usuário</label>
            </div>
            <div class="form-floating">
                <input type="password" class="form-control" id="password" name="password" placeholder="Senha" required>
                <label for="password">Senha</label>
            </div>
            
            <button class="w-100 btn btn-lg btn-primary" type="submit">Entrar</button>
            <p class="mt-5 mb-3 text-muted">&copy; WhatsApp Messenger Admin</p>
        </form>
    </main>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>""")
    
    # E um dashboard básico
    dashboard_template = os.path.join(template_dir, "dashboard.html")
    if not os.path.exists(dashboard_template):
        with open(dashboard_template, 'w') as f:
            f.write("""<!DOCTYPE html>
<html>
<head>
    <title>Dashboard - WhatsApp Messenger Admin</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.3/font/bootstrap-icons.css">
    <style>
        body {
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        .sidebar {
            background-color: #f8f9fa;
            min-height: calc(100vh - 56px);
        }
        .content {
            padding: 20px;
        }
        .server-card {
            transition: all 0.3s;
        }
        .server-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        @media (max-width: 768px) {
            .sidebar {
                min-height: auto;
            }
        }
    </style>
</head>
<body>
    <!-- Navbar -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container-fluid">
            <a class="navbar-brand" href="{{ url_for('dashboard') }}">WhatsApp Messenger Admin</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav me-auto">
                    <li class="nav-item">
                        <a class="nav-link active" href="{{ url_for('dashboard') }}">Dashboard</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('logs') }}">Logs</a>
                    </li>
                    {% if role == 'admin' %}
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('users') }}">Usuários</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('backup') }}">Backup</a>
                    </li>
                    {% endif %}
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('settings') }}">Configurações</a>
                    </li>
                </ul>
                <span class="navbar-text me-3">
                    Olá, {{ username }}
                </span>
                <a href="{{ url_for('logout') }}" class="btn btn-outline-light btn-sm">Sair</a>
            </div>
        </div>
    </nav>

    <!-- Conteúdo principal -->
    <div class="container-fluid flex-grow-1">
        <div class="row">
            <!-- Sidebar -->
            <div class="col-md-3 col-lg-2 d-md-block sidebar collapse">
                <div class="position-sticky pt-3">
                    <ul class="nav flex-column">
                        <li class="nav-item">
                            <a class="nav-link active" href="{{ url_for('dashboard') }}">
                                <i class="bi bi-speedometer2"></i> Dashboard
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="{{ url_for('analyze') }}">
                                <i class="bi bi-telephone"></i> Análise de Números
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="{{ url_for('logs') }}">
                                <i class="bi bi-file-text"></i> Logs
                            </a>
                        </li>
                        {% if role == 'admin' %}
                        <li class="nav-item">
                            <a class="nav-link" href="{{ url_for('users') }}">
                                <i class="bi bi-people"></i> Usuários
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="{{ url_for('backup') }}">
                                <i class="bi bi-archive"></i> Backup
                            </a>
                        </li>
                        {% endif %}
                        <li class="nav-item">
                            <a class="nav-link" href="{{ url_for('settings') }}">
                                <i class="bi bi-gear"></i> Configurações
                            </a>
                        </li>
                    </ul>
                </div>
            </div>

            <!-- Conteúdo principal -->
            <main class="col-md-9 ms-sm-auto col-lg-10 px-md-4 content">
                <div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
                    <h1 class="h2">Dashboard</h1>
                </div>

                <!-- Mensagens de alerta -->
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        {% for category, message in messages %}
                            <div class="alert alert-{{ category }} alert-dismissible fade show">
                                {{ message }}
                                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                            </div>
                        {% endfor %}
                    {% endif %}
                {% endwith %}

                <!-- Status do Servidor -->
                <div class="row mb-4">
                    <div class="col-md-4">
                        <div class="card server-card h-100 {% if server_status.running %}border-success{% else %}border-danger{% endif %}">
                            <div class="card-body">
                                <h5 class="card-title">Status do Servidor</h5>
                                {% if server_status.running %}
                                    <p class="text-success"><i class="bi bi-check-circle-fill"></i> Servidor rodando</p>
                                    <p>PID: {{ server_status.pid }}</p>
                                    <p>Uptime: {{ "%d:%02d:%02d"|format(server_status.uptime//3600, (server_status.uptime//60)%60, server_status.uptime%60) }}</p>
                                {% else %}
                                    <p class="text-danger"><i class="bi bi-x-circle-fill"></i> Servidor parado</p>
                                {% endif %}
                                <div class="d-flex justify-content-between mt-3">
                                    {% if server_status.running %}
                                        <button id="btnStopServer" class="btn btn-danger btn-sm">Parar Servidor</button>
                                    {% else %}
                                        <button id="btnStartServer" class="btn btn-success btn-sm">Iniciar Servidor</button>
                                    {% endif %}
                                    <button id="btnCheckStatus" class="btn btn-info btn-sm">Atualizar Status</button>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card server-card h-100 {% if server_status.whatsapp_connected %}border-success{% else %}border-warning{% endif %}">
                            <div class="card-body">
                                <h5 class="card-title">WhatsApp</h5>
                                {% if server_status.whatsapp_connected %}
                                    <p class="text-success"><i class="bi bi-check-circle-fill"></i> Conectado e pronto</p>
                                    <button id="btnResetWhatsapp" class="btn btn-warning btn-sm">Reiniciar Sessão</button>
                                {% else %}
                                    <p class="text-warning"><i class="bi bi-exclamation-circle-fill"></i> Não conectado</p>
                                    {% if server_status.running %}
                                        <button id="btnWhatsappLogin" class="btn btn-primary btn-sm">Conectar WhatsApp</button>
                                    {% else %}
                                        <p class="text-muted">Inicie o servidor para conectar o WhatsApp.</p>
                                    {% endif %}
                                {% endif %}
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card server-card h-100">
                            <div class="card-body">
                                <h5 class="card-title">Uso de Recursos</h5>
                                <div class="mb-2">
                                    <label class="form-label mb-0">CPU: {{ system_stats.cpu_percent }}%</label>
                                    <div class="progress">
                                        <div class="progress-bar" role="progressbar" style="width: {{ system_stats.cpu_percent }}%"></div>
                                    </div>
                                </div>
                                <div class="mb-2">
                                    <label class="form-label mb-0">Memória: {{ system_stats.memory_percent }}%</label>
                                    <div class="progress">
                                        <div class="progress-bar bg-warning" role="progressbar" style="width: {{ system_stats.memory_percent }}%"></div>
                                    </div>
                                </div>
                                <div>
                                    <label class="form-label mb-0">Disco: {{ system_stats.disk_percent }}%</label>
                                    <div class="progress">
                                        <div class="progress-bar bg-info" role="progressbar" style="width: {{ system_stats.disk_percent }}%"></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- QR Code (se necessário) -->
                {% if not server_status.whatsapp_connected and server_status.running and qr_info.available %}
                <div class="row mb-4">
                    <div class="col-md-6 mx-auto">
                        <div class="card">
                            <div class="card-header bg-warning text-dark">
                                Escaneie o QR Code
                            </div>
                            <div class="card-body text-center">
                                <p>Abra o WhatsApp no seu telefone, toque em Menu ou Configurações e selecione WhatsApp Web. Aponte seu telefone para esta tela para capturar o código.</p>
                                <img src="{{ url_for('api_whatsapp_qrcode') }}" class="img-fluid" alt="QR Code">
                                <div class="mt-3">
                                    <button id="btnRefreshQr" class="btn btn-outline-primary btn-sm">Atualizar QR Code</button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                {% endif %}

                <!-- Formulário de Envio -->
                {% if server_status.whatsapp_connected %}
                <div class="row mb-4">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header bg-primary text-white">
                                Enviar Mensagem
                            </div>
                            <div class="card-body">
                                <form id="formSendMessage">
                                    <div class="mb-3">
                                        <label for="number" class="form-label">Número de Telefone</label>
                                        <input type="text" class="form-control" id="number" placeholder="Ex: 551199887766" required>
                                    </div>
                                    <div class="mb-3">
                                        <label for="message" class="form-label">Mensagem</label>
                                        <textarea class="form-control" id="message" rows="3" required></textarea>
                                    </div>
                                    <button type="submit" class="btn btn-primary">Enviar</button>
                                </form>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header bg-primary text-white">
                                Enviar Arquivo
                            </div>
                            <div class="card-body">
                                <form id="formSendFile" enctype="multipart/form-data">
                                    <div class="mb-3">
                                        <label for="fileNumber" class="form-label">Número de Telefone</label>
                                        <input type="text" class="form-control" id="fileNumber" name="number" placeholder="Ex: 551199887766" required>
                                    </div>
                                    <div class="mb-3">
                                        <label for="fileCaption" class="form-label">Legenda (opcional)</label>
                                        <input type="text" class="form-control" id="fileCaption" name="caption">
                                    </div>
                                    <div class="mb-3">
                                        <label for="file" class="form-label">Arquivo</label>
                                        <input type="file" class="form-control" id="file" name="file" required>
                                    </div>
                                    <button type="submit" class="btn btn-primary">Enviar Arquivo</button>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Envio em Lote -->
                <div class="row mb-4">
                    <div class="col-md-12">
                        <div class="card">
                            <div class="card-header bg-success text-white">
                                Envio em Lote
                            </div>
                            <div class="card-body">
                                <form id="formSendBatch" enctype="multipart/form-data">
                                    <div class="row">
                                        <div class="col-md-6">
                                            <div class="mb-3">
                                                <label for="batchFile" class="form-label">Arquivo de Contatos (CSV/XLSX)</label>
                                                <input type="file" class="form-control" id="batchFile" name="file" accept=".csv,.xlsx,.xls" required>
                                                <div class="form-text">Primeira coluna deve conter os números de telefone.</div>
                                            </div>
                                            <div class="mb-3">
                                                <label for="batchMessage" class="form-label">Mensagem</label>
                                                <textarea class="form-control" id="batchMessage" name="message" rows="3"></textarea>
                                            </div>
                                        </div>
                                        <div class="col-md-6">
                                            <div class="mb-3">
                                                <label for="batchAttachments" class="form-label">Anexos (opcional)</label>
                                                <input type="file" class="form-control" id="batchAttachments" name="attachments[]" multiple>
                                            </div>
                                            <div class="mb-3">
                                                <label for="batchInterval" class="form-label">Intervalo Entre Mensagens (segundos)</label>
                                                <input type="number" class="form-control" id="batchInterval" name="interval" value="3" min="1" max="60">
                                            </div>
                                            <div class="mb-3 form-check">
                                                <input type="checkbox" class="form-check-input" id="batchRandomDelay" name="random_delay" checked>
                                                <label class="form-check-label" for="batchRandomDelay">Adicionar variação aleatória ao intervalo</label>
                                            </div>
                                        </div>
                                    </div>
                                    <button type="submit" class="btn btn-success">Iniciar Envio em Lote</button>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>
                {% endif %}

                <!-- Estatísticas -->
                <div class="row mb-4">
                    <div class="col-md-4">
                        <div class="card text-white bg-primary">
                            <div class="card-body">
                                <h5 class="card-title">Mensagens Enviadas</h5>
                                <p class="card-text display-4">{{ server_status.messages_sent_session }}</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card text-white bg-success">
                            <div class="card-body">
                                <h5 class="card-title">Arquivos Enviados</h5>
                                <p class="card-text display-4">{{ server_status.files_sent_session }}</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card text-white bg-danger">
                            <div class="card-body">
                                <h5 class="card-title">Erros</h5>
                                <p class="card-text display-4">{{ server_status.errors_session }}</p>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/jquery@3.6.3/dist/jquery.min.js"></script>
    <script>
        $(document).ready(function() {
            // Iniciar servidor
            $('#btnStartServer').click(function() {
                $.ajax({
                    url: '/api/server/start',
                    method: 'POST',
                    contentType: 'application/json',
                    data: JSON.stringify({}),
                    success: function(response) {
                        alert('Servidor iniciado. Recarregando página...');
                        location.reload();
                    },
                    error: function() {
                        alert('Erro ao iniciar servidor');
                    }
                });
            });

            // Parar servidor
            $('#btnStopServer').click(function() {
                if (confirm('Tem certeza que deseja parar o servidor?')) {
                    $.ajax({
                        url: '/api/server/stop',
                        method: 'POST',
                        contentType: 'application/json',
                        success: function(response) {
                            alert('Servidor parado. Recarregando página...');
                            location.reload();
                        },
                        error: function() {
                            alert('Erro ao parar servidor');
                        }
                    });
                }
            });

            // Verificar status
            $('#btnCheckStatus').click(function() {
                location.reload();
            });

            // Conectar WhatsApp
            $('#btnWhatsappLogin').click(function() {
                $.ajax({
                    url: '/api/whatsapp/login',
                    method: 'POST',
                    contentType: 'application/json',
                    success: function(response) {
                        alert('Solicitação de login enviada. Recarregando página...');
                        location.reload();
                    },
                    error: function() {
                        alert('Erro ao solicitar login');
                    }
                });
            });

            // Reiniciar sessão
            $('#btnResetWhatsapp').click(function() {
                if (confirm('Tem certeza que deseja reiniciar a sessão do WhatsApp? Você precisará escanear um novo QR code.')) {
                    $.ajax({
                        url: '/api/whatsapp/reset',
                        method: 'POST',
                        contentType: 'application/json',
                        success: function(response) {
                            alert('Sessão reiniciada. Recarregando página...');
                            location.reload();
                        },
                        error: function() {
                            alert('Erro ao reiniciar sessão');
                        }
                    });
                }
            });

            // Atualizar QR Code
            $('#btnRefreshQr').click(function() {
                location.reload();
            });

            // Enviar mensagem
            $('#formSendMessage').submit(function(e) {
                e.preventDefault();
                $.ajax({
                    url: '/api/message/send-text',
                    method: 'POST',
                    contentType: 'application/json',
                    data: JSON.stringify({
                        number: $('#number').val(),
                        message: $('#message').val()
                    }),
                    success: function(response) {
                        if (response.success) {
                            alert('Mensagem enviada com sucesso!');
                            $('#number').val('');
                            $('#message').val('');
                        } else {
                            alert('Erro ao enviar mensagem: ' + response.error);
                        }
                    },
                    error: function() {
                        alert('Erro ao enviar mensagem');
                    }
                });
            });

            // Enviar arquivo
            $('#formSendFile').submit(function(e) {
                e.preventDefault();
                var formData = new FormData(this);
                $.ajax({
                    url: '/api/message/send-file',
                    method: 'POST',
                    data: formData,
                    processData: false,
                    contentType: false,
                    success: function(response) {
                        if (response.success) {
                            alert('Arquivo enviado com sucesso!');
                            $('#fileNumber').val('');
                            $('#fileCaption').val('');
                            $('#file').val('');
                        } else {
                            alert('Erro ao enviar arquivo: ' + response.error);
                        }
                    },
                    error: function() {
                        alert('Erro ao enviar arquivo');
                    }
                });
            });

            // Envio em lote
            $('#formSendBatch').submit(function(e) {
                e.preventDefault();
                if (!confirm('Tem certeza que deseja iniciar o envio em lote?')) {
                    return;
                }
                
                var formData = new FormData(this);
                $.ajax({
                    url: '/api/message/send-batch',
                    method: 'POST',
                    data: formData,
                    processData: false,
                    contentType: false,
                    success: function(response) {
                        if (response.success) {
                            alert('Envio em lote iniciado em segundo plano!');
                            $('#batchFile').val('');
                            $('#batchMessage').val('');
                            $('#batchAttachments').val('');
                        } else {
                            alert('Erro ao iniciar envio em lote: ' + response.error);
                        }
                    },
                    error: function() {
                        alert('Erro ao iniciar envio em lote');
                    }
                });
            });
        });
    </script>
</body>
</html>""")
    
    # Cria os outros templates (não vou incluir todo o conteúdo por limitação de espaço)
    other_templates = ['users.html', 'logs.html', 'settings.html', 'backup.html', 'analyze.html']
    for template in other_templates:
        template_path = os.path.join(template_dir, template)
        if not os.path.exists(template_path):
            with open(template_path, 'w') as f:
                f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>{template.split('.')[0].capitalize()} - WhatsApp Messenger Admin</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <h1>Template placeholder para {template}</h1>
    <p>Este é um template básico. Implemente conforme necessário.</p>
    <a href="{{ url_for('dashboard') }}">Voltar para Dashboard</a>
</body>
</html>""")

if __name__ == "__main__":
    # Garantir que os diretórios de templates existam
    create_template_dirs()
    
    # Argumentos de linha de comando
    import argparse
    parser = argparse.ArgumentParser(description='Painel Administrativo WhatsApp Messenger')
    parser.add_argument('--host', default='0.0.0.0', help='Host para o servidor (padrão: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8080, help='Porta para o servidor (padrão: 8080)')
    parser.add_argument('--debug', action='store_true', help='Ativar modo de debug')
    args = parser.parse_args()
    
    # Iniciar servidor
    print(f"Iniciando painel administrativo em http://{args.host}:{args.port}")
    print("Credenciais padrão: admin / admin123")
    app.run(host=args.host, port=args.port, debug=args.debug)
