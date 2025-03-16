import os
import sys

# Patch para corrigir o erro de importação tkinter antes de qualquer outra importação
print("Inicializando aplicação...")
try:
    import tkinter_patch
    print("Patch tkinter carregado com sucesso")
except ImportError as e:
    print(f"Aviso: tkinter_patch não encontrado, aplicando correção manual: {e}")
    try:
        # Correção manual
        sys.modules['tkinter:filedialog'] = __import__('tkinter.filedialog', fromlist=[''])
        sys.modules['tkinter:messagebox'] = __import__('tkinter.messagebox', fromlist=[''])
        sys.modules['tkinter:scrolledtext'] = __import__('tkinter.scrolledtext', fromlist=[''])
        print("Patch manual aplicado")
    except Exception as e:
        print(f"Erro ao aplicar patch manual: {e}")

# Continua com as importações normais
import subprocess
import time
import threading
import json
import shutil
import requests
import platform
import webbrowser
import signal

# Importações tkinter após o patch ser aplicado
import tkinter as tk
from tkinter import messagebox, filedialog, scrolledtext

# Resto do código normal...

# ==== Funções do programa ====
# Determina se estamos em um executável ou em modo de desenvolvimento
def is_bundled():
    return getattr(sys, 'frozen', False)

# Obtém o diretório base correto dependendo se estamos em um executável ou não
def get_base_dir():
    if is_bundled():
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def list_directory_structure(dir_path, output_file, level=0):
    """Lista a estrutura de diretórios para diagnóstico"""
    if not os.path.exists(dir_path):
        output_file.write(f"{'  ' * level}[NÃO EXISTE] {dir_path}\n")
        return
        
    if os.path.isfile(dir_path):
        output_file.write(f"{'  ' * level}[ARQUIVO] {os.path.basename(dir_path)}\n")
        return
        
    output_file.write(f"{'  ' * level}[PASTA] {os.path.basename(dir_path)}\n")
    
    try:
        entries = os.listdir(dir_path)
        for entry in sorted(entries):
            full_path = os.path.join(dir_path, entry)
            list_directory_structure(full_path, output_file, level + 1)
    except Exception as e:
        output_file.write(f"{'  ' * (level+1)}[ERRO AO LISTAR] {e}\n")

class DependencyInstaller:
    """Classe para instalar dependências Node.js automaticamente"""
    def __init__(self, master=None):
        self.master = master
        self.installing = False
        self.progress_window = None
        self.progress_text = None
        self.progress_bar = None
        self.npm_cmd = "npm"  # Comando padrão
        self.complete_callback = None
        self.status_callback = None
        
    def check_and_install_deps(self, server_dir, callback=None, status_callback=None):
        """Verifica se as dependências estão instaladas e instala se necessário"""
        self.complete_callback = callback
        self.status_callback = status_callback
        
        # Verifica se node_modules existe e contém as dependências essenciais
        node_modules_dir = os.path.join(server_dir, "node_modules")
        package_json = os.path.join(server_dir, "package.json")
        
        if not os.path.exists(package_json):
            self._update_status("Erro: package.json não encontrado!")
            return False
            
        missing_deps = True
        
        # Verifica se as principais dependências estão instaladas
        if os.path.exists(node_modules_dir):
            print(f"Verificando módulos em {node_modules_dir}")
            modules = os.listdir(node_modules_dir)
            required_modules = ["express", "whatsapp-web.js", "cors", "body-parser", "multer", "qrcode-terminal"]
            
            # Verifica se todos os módulos necessários estão presentes
            missing_modules = [m for m in required_modules if m not in modules]
            
            if not missing_modules:
                print("Todas as dependências estão instaladas")
                missing_deps = False
                if self.complete_callback:
                    self.complete_callback(True)
                return True
            else:
                print(f"Módulos faltando: {missing_modules}")
        
        if missing_deps:
            print("Dependências faltando. Iniciando instalação automática...")
            self._show_progress_window()
            threading.Thread(target=self._install_dependencies, args=(server_dir,), daemon=True).start()
        
        return True
    
    def _find_npm_command(self):
        """Encontra o comando npm disponível no sistema"""
        # Primeiro tenta o npm padrão
        try:
            subprocess.run(["npm", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return "npm"
        except:
            print("npm não encontrado no PATH")
        
        # Tenta localizar npm em locais comuns
        base_dir = get_base_dir()
        
        # Verificar no diretório bin/node
        if platform.system() == "Windows":
            npm_path = os.path.join(base_dir, "bin", "node", "npm.cmd")
            if os.path.exists(npm_path):
                return npm_path
            
            # Tenta outras localizações comuns no Windows
            for path in [
                os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "nodejs", "npm.cmd"),
                os.path.join(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"), "nodejs", "npm.cmd"),
                os.path.join(os.environ.get("APPDATA", ""), "npm", "npm.cmd")
            ]:
                if os.path.exists(path):
                    return path
        else:
            # Em sistemas Unix
            for path in ["/usr/local/bin/npm", "/usr/bin/npm", "/opt/local/bin/npm"]:
                if os.path.exists(path):
                    return path
        
        print("npm não encontrado em localizações comuns")
        return "npm"  # Retorna o padrão como último recurso
    
    def _show_progress_window(self):
        """Mostra uma janela com progresso da instalação"""
        if self.master is None:
            return
            
        self.progress_window = tk.Toplevel(self.master)
        self.progress_window.title("Instalando Dependências")
        self.progress_window.geometry("400x300")
        self.progress_window.transient(self.master)
        self.progress_window.grab_set()
        
        # Mensagem explicativa
        message = (
            "Instalando dependências necessárias...\n\n"
            "Este processo acontece apenas na primeira execução\n"
            "e pode levar alguns minutos.\n\n"
            "Por favor, aguarde até a conclusão."
        )
        
        tk.Label(self.progress_window, text=message, justify=tk.CENTER, padx=20, pady=20).pack()
        
        # Barra de progresso indeterminada
        self.progress_bar = tk.Canvas(self.progress_window, width=300, height=20, bg="white")
        self.progress_bar.pack(pady=10)
        self.progress_bar.create_rectangle(0, 0, 20, 20, fill="blue", tags="progress")
        
        # Área de texto para log
        self.progress_text = tk.Text(self.progress_window, height=10, width=45)
        self.progress_text.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
        
        # Inicia animação da barra de progresso
        self._animate_progress()
    
    def _animate_progress(self):
        """Anima a barra de progresso"""
        if not self.progress_bar or not self.progress_window:
            return
            
        try:
            # Move o retângulo azul da esquerda para a direita
            x = self.progress_bar.coords("progress")[0]
            if x > 300:
                self.progress_bar.coords("progress", 0, 0, 20, 20)
            else:
                self.progress_bar.move("progress", 5, 0)
                
            # Agendar próxima animação se a janela ainda existir
            if self.progress_window:
                self.progress_window.after(50, self._animate_progress)
        except:
            # Ignora erros se a janela foi fechada
            pass
    
    def _update_progress_text(self, text):
        """Atualiza o texto de progresso"""
        if self.progress_text:
            self.progress_text.insert(tk.END, text + "\n")
            self.progress_text.see(tk.END)
        
        # Também atualiza o status externo, se disponível
        if self.status_callback:
            self.status_callback(text)
    
    def _update_status(self, text):
        """Atualiza apenas o status externo"""
        if self.status_callback:
            self.status_callback(text)
        print(text)
    
    def _install_dependencies(self, server_dir):
        """Instala as dependências Node.js"""
        self.installing = True
        success = False
        
        try:
            # Encontra o comando npm
            self.npm_cmd = self._find_npm_command()
            self._update_progress_text(f"Usando npm: {self.npm_cmd}")
            
            # Tenta instalar as dependências
            self._update_progress_text("Iniciando instalação de dependências...")
            
            # Em uma máquina sem npm, podemos tentar instalar com o Node.js incluído no pacote
            node_modules_dir = os.path.join(server_dir, "node_modules")
            if not os.path.exists(node_modules_dir):
                os.makedirs(node_modules_dir)
            
            # Prepara o ambiente para o subprocess
            env = os.environ.copy()
            
            # No Windows, adiciona o caminho do Node.js ao PATH
            if platform.system() == "Windows":
                node_dir = os.path.join(get_base_dir(), "bin", "node")
                if os.path.exists(node_dir):
                    env["PATH"] = node_dir + os.pathsep + env.get("PATH", "")
            
            # Executa npm install
            process = subprocess.Popen(
                [self.npm_cmd, "install"],
                cwd=server_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=env
            )
            
            # Lê a saída em tempo real
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    self._update_progress_text(output.strip())
            
            # Verifica o resultado
            if process.returncode == 0:
                self._update_progress_text("Instalação concluída com sucesso!")
                success = True
            else:
                self._update_progress_text(f"Erro ao instalar dependências, código: {process.returncode}")
                
            # Verifica novamente se as dependências foram instaladas
            if os.path.exists(node_modules_dir):
                modules = os.listdir(node_modules_dir)
                required_modules = ["express", "whatsapp-web.js", "cors", "body-parser", "multer", "qrcode-terminal"]
                missing_modules = [m for m in required_modules if m not in modules]
                
                if not missing_modules:
                    self._update_progress_text("Todas as dependências foram instaladas corretamente!")
                    success = True
                else:
                    self._update_progress_text(f"Algumas dependências ainda estão faltando: {missing_modules}")
                    success = False
        
        except Exception as e:
            self._update_progress_text(f"Erro durante a instalação: {str(e)}")
            success = False
            
        self.installing = False
        
        # Fecha a janela após 2 segundos se bem-sucedido
        if success and self.progress_window:
            self._update_progress_text("Fechando esta janela em 2 segundos...")
            if self.progress_window:
                self.progress_window.after(2000, self.progress_window.destroy)
        
        # Chama o callback com o resultado
        if self.complete_callback:
            self.complete_callback(success)

class ServerProcess:
    def __init__(self):
        self.process = None
        self.is_running = False
        self.log_file = None
        self.dependency_installer = None

    def start(self, dependency_check=True, master=None):
        if self.is_running:
            return True
        
        base_dir = get_base_dir()
        
        # Configura o ambiente
        env = os.environ.copy()
        
        # Diretório do servidor
        server_dir = os.path.join(base_dir, "server")
        
        # Log para debugging
        log_path = os.path.join(base_dir, "server_log.txt")
        self.log_file = open(log_path, "w")
        
        self.log_file.write(f"Base dir: {base_dir}\n")
        self.log_file.write(f"Server dir: {server_dir}\n")
        self.log_file.flush()
        
        # Verifica se os diretórios existem e os cria se necessário
        if not os.path.exists(server_dir):
            os.makedirs(server_dir)
            self.log_file.write(f"Criado diretório do servidor: {server_dir}\n")
        
        # Verifica e instala dependências automaticamente se necessário
        if dependency_check:
            self.log_file.write("Verificando dependências do servidor...\n")
            self.log_file.flush()
            
            # Verifica se package.json existe
            package_json = os.path.join(server_dir, "package.json")
            if not os.path.exists(package_json):
                self.log_file.write(f"ERRO: package.json não encontrado em {package_json}\n")
                
                # Procura package.json em outros lugares
                for root, dirs, files in os.walk(base_dir):
                    for file in files:
                        if file == "package.json":
                            package_json_found = os.path.join(root, file)
                            self.log_file.write(f"package.json encontrado em: {package_json_found}\n")
                            try:
                                shutil.copy2(package_json_found, package_json)
                                self.log_file.write(f"package.json copiado para: {package_json}\n")
                                break
                            except Exception as e:
                                self.log_file.write(f"Erro ao copiar package.json: {e}\n")
            
            # Verifica node_modules
            node_modules_dir = os.path.join(server_dir, "node_modules")
            if not os.path.exists(node_modules_dir) or not os.listdir(node_modules_dir):
                self.log_file.write(f"node_modules não encontrado ou vazio em {node_modules_dir}. Instalando dependências automaticamente...\n")
                self.log_file.flush()
                
                # Instala dependências automaticamente
                self.dependency_installer = DependencyInstaller(master)
                
                def log_status(message):
                    self.log_file.write(f"{message}\n")
                    self.log_file.flush()
                
                def on_deps_installed(success):
                    if success:
                        self.log_file.write("Dependências instaladas com sucesso!\n")
                        # Continua o processo de inicialização do servidor
                        self._continue_start(server_dir, env)
                    else:
                        self.log_file.write("Falha ao instalar dependências.\n")
                        if master:
                            master.after(0, lambda: messagebox.showerror(
                                "Erro de Dependências", 
                                "Não foi possível instalar as dependências necessárias.\n" +
                                "O aplicativo pode não funcionar corretamente."
                            ))
                
                # Inicia a verificação e instalação
                self.dependency_installer.check_and_install_deps(
                    server_dir,
                    callback=on_deps_installed,
                    status_callback=log_status
                )
                
                # Retorna False para indicar que o servidor não foi iniciado ainda
                # mas está em processo de instalação de dependências
                return False
            else:
                self.log_file.write(f"node_modules encontrado em {node_modules_dir}. Verificando dependências...\n")
                # Verifica se as dependências principais estão presentes
                modules = os.listdir(node_modules_dir)
                required_modules = ["express", "whatsapp-web.js", "cors", "body-parser", "multer", "qrcode-terminal"]
                missing_modules = [m for m in required_modules if m not in modules]
                
                if missing_modules:
                    self.log_file.write(f"Alguns módulos necessários estão faltando: {missing_modules}. Instalando dependências...\n")
                    self.log_file.flush()
                    
                    # Instala dependências automaticamente
                    self.dependency_installer = DependencyInstaller(master)
                    
                    def log_status(message):
                        self.log_file.write(f"{message}\n")
                        self.log_file.flush()
                    
                    def on_deps_installed(success):
                        if success:
                            self.log_file.write("Dependências instaladas com sucesso!\n")
                            # Continua o processo de inicialização do servidor
                            self._continue_start(server_dir, env)
                        else:
                            self.log_file.write("Falha ao instalar dependências.\n")
                            if master:
                                master.after(0, lambda: messagebox.showerror(
                                    "Erro de Dependências", 
                                    "Não foi possível instalar as dependências necessárias.\n" +
                                    "O aplicativo pode não funcionar corretamente."
                                ))
                    
                    # Inicia a verificação e instalação
                    self.dependency_installer.check_and_install_deps(
                        server_dir,
                        callback=on_deps_installed,
                        status_callback=log_status
                    )
                    
                    # Retorna False para indicar que o servidor não foi iniciado ainda
                    # mas está em processo de instalação de dependências
                    return False
        
        # Se não precisar verificar dependências ou elas já estiverem instaladas,
        # continua o processo normalmente
        return self._continue_start(server_dir, env)

    def _continue_start(self, server_dir, env):
        """Continua o processo de inicialização do servidor após verificação de dependências"""
        # Comando para iniciar o servidor Node.js
        if platform.system() == "Windows":
            # No Windows, executamos "node server.js"
            node_path = os.path.join(get_base_dir(), "bin", "node", "node.exe")
            server_js = os.path.join(server_dir, "server.js")
            
            # Verificações adicionais para arquivos essenciais
            if not os.path.exists(node_path):
                self.log_file.write(f"ERRO: node.exe não encontrado em {node_path}\n")
                self.log_file.write("Procurando node.exe em outros locais...\n")
                
                # Alternativa 1: Procurar no diretório bin
                alt_node_path = os.path.join(get_base_dir(), "bin", "node.exe")
                if os.path.exists(alt_node_path):
                    self.log_file.write(f"node.exe encontrado em: {alt_node_path}\n")
                    node_path = alt_node_path
                else:
                    # Alternativa 2: Usar o Node.js instalado no sistema
                    self.log_file.write("Tentando usar Node.js do sistema...\n")
                    node_path = "node"
            
            if not os.path.exists(server_js):
                self.log_file.write(f"ERRO: server.js não encontrado em {server_js}\n")
                # Verificar se existe um arquivo chamado server.js em qualquer lugar
                for root, dirs, files in os.walk(get_base_dir()):
                    for file in files:
                        if file == "server.js":
                            server_js_found = os.path.join(root, file)
                            self.log_file.write(f"server.js encontrado em: {server_js_found}\n")
                            try:
                                # Tenta copiar o arquivo
                                shutil.copy2(server_js_found, server_js)
                                self.log_file.write(f"server.js copiado para: {server_js}\n")
                                break
                            except Exception as e:
                                self.log_file.write(f"Erro ao copiar server.js: {e}\n")
            
            self.log_file.write(f"Node path: {node_path}\n")
            self.log_file.write(f"Server.js path: {server_js}\n")
            self.log_file.write(f"Node exists: {os.path.exists(node_path)}\n")
            self.log_file.write(f"Server.js exists: {os.path.exists(server_js)}\n")
            self.log_file.flush()
            
            cmd = [node_path, server_js]
        else:
            # Em outros sistemas, podemos tentar usar o node do sistema
            server_js = os.path.join(server_dir, "server.js")
            
            # Verificação para o server.js
            if not os.path.exists(server_js):
                self.log_file.write(f"ERRO: server.js não encontrado em {server_js}\n")
                # Busca pelo arquivo em outros lugares
                for root, dirs, files in os.walk(get_base_dir()):
                    for file in files:
                        if file == "server.js":
                            server_js_found = os.path.join(root, file)
                            self.log_file.write(f"server.js encontrado em: {server_js_found}\n")
                            try:
                                # Tenta copiar o arquivo
                                shutil.copy2(server_js_found, server_js)
                                self.log_file.write(f"server.js copiado para: {server_js}\n")
                                break
                            except Exception as e:
                                self.log_file.write(f"Erro ao copiar server.js: {e}\n")
            
            cmd = ["node", server_js]
        
        # Definir o diretório de trabalho correto
        working_dir = server_dir
        
        # Inicia o processo do servidor
        try:
            self.log_file.write(f"Tentando iniciar o servidor com comando: {cmd}\n")
            self.log_file.write(f"Diretório de trabalho: {working_dir}\n")
            self.log_file.flush()
            
            self.process = subprocess.Popen(
                cmd,
                cwd=working_dir,
                stdout=self.log_file,
                stderr=self.log_file,
                env=env
            )
            self.is_running = True
            self.log_file.write(f"Servidor iniciado (PID: {self.process.pid})\n")
            self.log_file.flush()
            print(f"Servidor iniciado (PID: {self.process.pid})")
            return True
        except Exception as e:
            self.log_file.write(f"Erro ao iniciar o servidor: {e}\n")
            self.log_file.flush()
            print(f"Erro ao iniciar o servidor: {e}")
            return False

    def stop(self):
        if not self.is_running or not self.process:
            return
        
        try:
            if platform.system() == "Windows":
                # No Windows, usamos taskkill para garantir que todos os processos filho sejam encerrados
                subprocess.call(['taskkill', '/F', '/T', '/PID', str(self.process.pid)])
            else:
                # Em sistemas Unix, podemos enviar um sinal SIGTERM
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                self.process.terminate()
                
            self.process.wait(timeout=5)  # Espera até 5 segundos para o processo terminar
            
        except subprocess.TimeoutExpired:
            # Se o processo não terminar após o timeout, força o encerramento
            if platform.system() == "Windows":
                subprocess.call(['taskkill', '/F', '/T', '/PID', str(self.process.pid)])
            else:
                os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                self.process.kill()
        except Exception as e:
            print(f"Erro ao encerrar o servidor: {e}")
        
        self.is_running = False
        
        if self.log_file:
            self.log_file.close()
            self.log_file = None
        
        print("Servidor encerrado")

    def is_alive(self):
        if not self.process:
            return False
        return self.process.poll() is None

class LauncherApp:
    def __init__(self, root):
        self.root = root
        self.server = ServerProcess()
        self.setup_ui()
        
        # Inicia automaticamente o servidor e o cliente
        self.root.after(500, self.start_application)

    def setup_ui(self):
        self.root.title("WhatsApp Messenger Launcher")
        self.root.geometry("400x300")
        self.root.configure(bg="#f5f5f5")
        
        # Estilo
        title_font = ("Helvetica", 16, "bold")
        button_font = ("Helvetica", 10)
        
        # Título
        title_label = tk.Label(
            self.root, 
            text="WhatsApp Messenger", 
            font=title_font,
            bg="#f5f5f5", 
            fg="#333333"
        )
        title_label.pack(pady=20)
        
        # Frame para status
        status_frame = tk.Frame(self.root, bg="#f5f5f5")
        status_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.status_label = tk.Label(
            status_frame, 
            text="Iniciando...", 
            bg="#f5f5f5", 
            fg="#333333"
        )
        self.status_label.pack(side=tk.LEFT)
        
        self.status_indicator = tk.Label(
            status_frame, 
            text="⬤", 
            font=("Helvetica", 12),
            bg="#f5f5f5", 
            fg="orange"
        )
        self.status_indicator.pack(side=tk.RIGHT)
        
        # Frame para botões
        button_frame = tk.Frame(self.root, bg="#f5f5f5")
        button_frame.pack(pady=20)
        
        # Botão para iniciar a aplicação
        self.start_button = tk.Button(
            button_frame,
            text="Iniciar Aplicação",
            command=self.start_application,
            width=20,
            font=button_font,
            bg="#4CAF50",
            fg="white",
            relief=tk.FLAT
        )
        self.start_button.pack(pady=5)
        
        # Botão para reiniciar sessão
        self.reset_button = tk.Button(
            button_frame,
            text="Reiniciar Sessão WhatsApp",
            command=self.reset_whatsapp_session,
            width=20,
            font=button_font,
            bg="#2196F3",
            fg="white",
            relief=tk.FLAT,
            state=tk.DISABLED
        )
        self.reset_button.pack(pady=5)
        
        # Botão para encerrar a aplicação
        self.stop_button = tk.Button(
            button_frame,
            text="Encerrar Aplicação",
            command=self.stop_application,
            width=20,
            font=button_font,
            bg="#F44336",
            fg="white",
            relief=tk.FLAT,
            state=tk.DISABLED
        )
        self.stop_button.pack(pady=5)
        
        # Botão para verificação de arquivos
        self.debug_button = tk.Button(
            button_frame,
            text="Verificar e Instalar",
            command=self.check_and_install_dependencies,
            width=20,
            font=button_font,
            bg="#FF9800",
            fg="white",
            relief=tk.FLAT
        )
        self.debug_button.pack(pady=5)
        
        # Versão
        version_label = tk.Label(
            self.root, 
            text="v1.0.0", 
            bg="#f5f5f5", 
            fg="#999999",
            font=("Helvetica", 8)
        )
        version_label.pack(side=tk.BOTTOM, pady=10)
        
        # Adiciona um handler para o fechamento da janela
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def update_status(self, message, color="black"):
        self.status_label.config(text=message)
        self.status_indicator.config(fg=color)

    def start_application(self):
        self.update_status("Iniciando servidor...", "orange")
        self.start_button.config(state=tk.DISABLED)
        
        # Inicia o servidor em uma thread separada
        threading.Thread(target=self._start_server, daemon=True).start()

    def check_and_install_dependencies(self):
        """Verifica e instala as dependências necessárias manualmente"""
        self.update_status("Verificando dependências...", "orange")
        
        base_dir = get_base_dir()
        server_dir = os.path.join(base_dir, "server")
        
        if not os.path.exists(server_dir):
            os.makedirs(server_dir)
        
        # Verifica se server.js e package.json existem
        server_js = os.path.join(server_dir, "server.js")
        package_json = os.path.join(server_dir, "package.json")
        
        missing_files = []
        
        if not os.path.exists(server_js):
            missing_files.append("server.js")
        
        if not os.path.exists(package_json):
            missing_files.append("package.json")
        
        if missing_files:
            messagebox.showerror(
                "Arquivos Ausentes", 
                f"Os seguintes arquivos estão faltando: {', '.join(missing_files)}\n\n"
                f"Verifique se os arquivos estão presentes em {server_dir}"
            )
            return
        
        # Cria janela de instalação de dependências
        self.installer = DependencyInstaller(self.root)
        
        def on_deps_installed(success):
            if success:
                self.update_status("Dependências instaladas", "green")
                messagebox.showinfo(
                    "Instalação Concluída", 
                    "As dependências foram instaladas com sucesso!\n\n"
                    "Agora você pode iniciar a aplicação."
                )
            else:
                self.update_status("Falha na instalação", "red")
                messagebox.showerror(
                    "Erro de Instalação", 
                    "Ocorreu um erro ao instalar as dependências.\n\n"
                    "Consulte os logs para mais detalhes."
                )
        
        def update_status(msg):
            self.update_status(f"Instalando: {msg}", "blue")
        
        # Inicia a instalação
        self.installer.check_and_install_deps(
            server_dir,
            callback=on_deps_installed,
            status_callback=update_status
        )

    def _start_server(self):
        # Inicia o servidor com verificação automática de dependências
        server_started = self.server.start(dependency_check=True, master=self.root)
        
        if not server_started:
            # Se o servidor não foi iniciado imediatamente, pode ser devido à instalação
            # de dependências em andamento. Nesse caso, não tratamos como erro ainda.
            print("Servidor não foi iniciado imediatamente. Pode estar instalando dependências...")
            
            # Verifica periodicamente se o servidor está rodando
            for _ in range(60):  # verificar por até 3 minutos (60 * 3 segundos)
                time.sleep(3)
                if self.server.is_running:
                    print("Servidor iniciado com sucesso após instalação de dependências")
                    self.root.after(0, lambda: self._check_server_ready())
                    return
            
            # Se após 3 minutos o servidor ainda não estiver rodando, mostra erro
            self.root.after(0, lambda: self._show_server_error())
            return
            
        # Se o servidor foi iniciado normalmente, verifica se está respondendo
        self.root.after(1000, self._check_server_ready)

    def _check_server_ready(self):
        """Verifica se o servidor está pronto e respondendo"""
        # Aguarda o servidor iniciar completamente (máximo 20 segundos)
        server_ready = False
        retries = 0
        while not server_ready and retries < 40:  # 40 tentativas com 0.5s de intervalo = 20s
            try:
                response = requests.get("http://localhost:3000/api/status", timeout=0.5)
                if response.status_code == 200:
                    server_ready = True
                    break
            except:
                pass
            time.sleep(0.5)
            retries += 1
        
        if not server_ready:
            self._show_server_error()
            return
        
        # Inicia a aplicação principal
        self.update_status("Iniciando a aplicação principal...", "green")
        self._start_main_app()

    def _show_server_error(self):
        """Mostra mensagem de erro do servidor"""
        self.update_status("Servidor não respondendo", "red")
        
        error_msg = (
            "O servidor não está respondendo. Isso pode ocorrer pelos seguintes motivos:\n\n"
            "1. Dependências do Node.js não estão instaladas\n"
            "2. O servidor encontrou erro ao iniciar\n\n"
            "Clique em 'Verificar e Instalar' para tentar resolver o problema."
        )
        
        messagebox.showerror("Erro", error_msg)
        self.server.stop()
        self.start_button.config(state=tk.NORMAL)

    def _start_main_app(self):
        # Importa o módulo da aplicação principal
        try:
            # Ativa os botões
            self.reset_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.NORMAL)
            
            # Importa e inicia a aplicação principal
            base_dir = get_base_dir()
            client_dir = os.path.join(base_dir, "client")
            
            # Adiciona o diretório do cliente ao path se existir
            if os.path.exists(client_dir):
                sys.path.append(client_dir)
                print(f"Adicionado ao path: {client_dir}")
            else:
                print(f"Diretório do cliente não encontrado: {client_dir}")
                # Verifica se existe o arquivo em uma pasta diferente
                app_file = None
                for root, dirs, files in os.walk(base_dir):
                    for file in files:
                        if file == "whatsapp_messenger.py":
                            app_file = os.path.join(root, file)
                            app_dir = root
                            sys.path.append(app_dir)
                            print(f"Encontrado whatsapp_messenger.py em: {app_file}")
                            print(f"Adicionado ao path: {app_dir}")
                            break
                    if app_file:
                        break
                if not app_file:
                    raise FileNotFoundError("whatsapp_messenger.py não encontrado")
            
            try:
                import whatsapp_messenger
            except ImportError as e:
                print(f"Erro ao importar whatsapp_messenger: {e}")
                # Tenta importar diretamente de um arquivo
                import importlib.util
                app_file = None
                for root, dirs, files in os.walk(base_dir):
                    for file in files:
                        if file == "whatsapp_messenger.py":
                            app_file = os.path.join(root, file)
                            break
                    if app_file:
                        break
                
                if app_file:
                    print(f"Importando diretamente de: {app_file}")
                    spec = importlib.util.spec_from_file_location("whatsapp_messenger", app_file)
                    whatsapp_messenger = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(whatsapp_messenger)
                else:
                    raise FileNotFoundError("whatsapp_messenger.py não encontrado")
            
            # Cria uma nova janela para a aplicação principal
            app_window = tk.Toplevel(self.root)
            self.app = whatsapp_messenger.WhatsAppMessengerGUI(app_window)
            
            # Minimiza a janela do launcher
            self.root.iconify()
            
            # Configura comportamento de fechamento da janela principal
            app_window.protocol("WM_DELETE_WINDOW", self.on_main_app_close)
            
            self.update_status("Aplicação iniciada com sucesso", "green")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.update_status(f"Erro ao iniciar aplicação", "red")
            messagebox.showerror("Erro", f"Erro ao iniciar a aplicação principal: {e}")
            print(f"Erro ao iniciar aplicação principal: {e}")
            self.start_button.config(state=tk.NORMAL)

    def on_main_app_close(self):
        # Quando a janela principal é fechada, mostramos o launcher novamente
        self.root.deiconify()
        self.update_status("Aplicação principal fechada", "orange")

    def reset_whatsapp_session(self):
        # Pergunta ao usuário se tem certeza
        if not messagebox.askyesno("Reiniciar Sessão", 
                                 "Isso irá encerrar sua sessão atual do WhatsApp.\n\n"
                                 "Você precisará escanear um novo QR code para reconectar.\n\n"
                                 "Deseja continuar?"):
            return
        
        # Tenta reiniciar a sessão do WhatsApp
        try:
            self.update_status("Reiniciando sessão do WhatsApp...", "orange")
            
            # Primeiro, tenta parar o servidor
            self.server.stop()
            time.sleep(2)
            
            # Depois, remove os arquivos de sessão do WhatsApp
            base_dir = get_base_dir()
            session_dir = os.path.join(base_dir, "server", "whatsapp-session")
            if os.path.exists(session_dir):
                try:
                    shutil.rmtree(session_dir)
                    print(f"Diretório de sessão removido: {session_dir}")
                except Exception as e:
                    print(f"Erro ao remover diretório de sessão: {e}")
            
            # Reinicia o servidor
            time.sleep(1)
            threading.Thread(target=self._start_server, daemon=True).start()
            
        except Exception as e:
            self.update_status("Erro ao reiniciar sessão", "red")
            messagebox.showerror("Erro", f"Falha ao reiniciar sessão: {e}")

    def stop_application(self):
        if messagebox.askyesno("Encerrar", "Deseja realmente encerrar a aplicação?"):
            self.on_close()

    def on_close(self):
        # Encerra o servidor e a aplicação
        self.update_status("Encerrando...", "red")
        
        try:
            # Tenta encerrar o servidor
            if self.server.is_running:
                self.server.stop()
        except Exception as e:
            print(f"Erro ao encerrar o servidor: {e}")
        
        self.root.destroy()
        sys.exit(0)

# Função principal
def main():
    # Diagnóstico da estrutura de diretórios
    base_dir = get_base_dir()
    with open(os.path.join(base_dir, "directory_structure.txt"), "w", encoding="utf-8") as f:
        f.write(f"Base directory: {base_dir}\n\n")
        f.write("Estrutura de diretórios:\n")
        list_directory_structure(base_dir, f)
    
    root = tk.Tk()
    app = LauncherApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()