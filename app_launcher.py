import os
import sys
import subprocess
import time
import tkinter as tk
import threading
import json
import shutil
import requests
from tkinter import messagebox
import platform
import webbrowser
import signal

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

class ServerProcess:
    def __init__(self):
        self.process = None
        self.is_running = False
        self.log_file = None

    def start(self):
        if self.is_running:
            return
        
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
        
        # Comando para iniciar o servidor Node.js
        if platform.system() == "Windows":
            # No Windows, executamos "node server.js"
            node_path = os.path.join(base_dir, "bin", "node", "node.exe")
            server_js = os.path.join(server_dir, "server.js")
            
            self.log_file.write(f"Node path: {node_path}\n")
            self.log_file.write(f"Server.js path: {server_js}\n")
            self.log_file.write(f"Node exists: {os.path.exists(node_path)}\n")
            self.log_file.write(f"Server.js exists: {os.path.exists(server_js)}\n")
            self.log_file.flush()
            
            cmd = [node_path, server_js]
        else:
            # Em outros sistemas, podemos tentar usar o node do sistema
            server_js = os.path.join(server_dir, "server.js")
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

    def _start_server(self):
        if not self.server.start():
            # Adicione estes logs para depuração
            log_path = os.path.join(get_base_dir(), "server_error_log.txt")
            with open(log_path, "w") as f:
                f.write(f"Erro ao iniciar o servidor\n")
                f.write(f"Base dir: {get_base_dir()}\n")
                f.write(f"Server dir: {os.path.join(get_base_dir(), 'server')}\n")
                # Verifique se os arquivos do servidor existem
                server_js = os.path.join(get_base_dir(), "server", "server.js")
                f.write(f"server.js existe: {os.path.exists(server_js)}\n")
                # Verifique caminho Node.js
                if platform.system() == "Windows":
                    node_path = os.path.join(get_base_dir(), "bin", "node", "node.exe")
                    f.write(f"node.exe existe: {os.path.exists(node_path)}\n")
            
            self.root.after(0, lambda: self.update_status("Falha ao iniciar o servidor", "red"))
            self.root.after(0, lambda: messagebox.showerror("Erro", "Falha ao iniciar o servidor."))
            self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))
            return
        
        # Aguarda o servidor iniciar completamente (máximo 10 segundos)
        server_ready = False
        for _ in range(20):  # 20 tentativas com 0.5s de intervalo = 10s
            try:
                response = requests.get("http://localhost:3000/api/status", timeout=0.5)
                if response.status_code == 200:
                    server_ready = True
                    break
            except:
                pass
            time.sleep(0.5)
        
        if not server_ready:
            self.root.after(0, lambda: self.update_status("Servidor não respondendo", "red"))
            self.root.after(0, lambda: messagebox.showerror("Erro", "Servidor não está respondendo."))
            self.server.stop()
            self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))
            return
        
        # Inicia a aplicação principal
        self.root.after(0, lambda: self.update_status("Iniciando a aplicação principal...", "green"))
        self.root.after(0, self._start_main_app)

    def _start_main_app(self):
        # Importa o módulo da aplicação principal
        try:
            # Ativa os botões
            self.reset_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.NORMAL)
            
            # Importa e inicia a aplicação principal
            base_dir = get_base_dir()
            sys.path.append(os.path.join(base_dir, "client"))
            
            import whatsapp_messenger
            
            # Cria uma nova janela para a aplicação principal
            app_window = tk.Toplevel(self.root)
            self.app = whatsapp_messenger.WhatsAppMessengerGUI(app_window)
            
            # Minimiza a janela do launcher
            self.root.iconify()
            
            # Configura comportamento de fechamento da janela principal
            app_window.protocol("WM_DELETE_WINDOW", self.on_main_app_close)
            
            self.update_status("Aplicação iniciada com sucesso", "green")
            
        except Exception as e:
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