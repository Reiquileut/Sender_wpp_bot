import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import pandas as pd
import time
import datetime
import threading
import os
import requests
import json
import random
import csv

# Importar ttkbootstrap para estilo moderno (necessário instalar: pip install ttkbootstrap)
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

def is_running_as_imported_module():
    """Verifica se o script está sendo executado como um módulo importado."""
    return __name__ != "__main__"

# Nome do arquivo de log
LOG_FILE = "log.txt"
# URL base da API (ajuste conforme necessário)
API_BASE_URL = "http://localhost:3000/api"

class WhatsAppMessengerGUI:
    def __init__(self, master):
        self.master = master
        master.title("WhatsApp Messenger Pro")
        master.geometry("800x800")
        
        # Configurar o estilo geral
        self.style = ttk.Style()
        
        # Frame principal com scrollbar
        main_frame = ttk.Frame(master)
        main_frame.pack(fill=tk.BOTH, expand=1)
        
        # Canvas e scrollbar
        canvas = tk.Canvas(main_frame, background="#f5f5f5")
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=780)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Adiciona a rolagem com a roda do mouse
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Frame de cabeçalho com logo e título
        header_frame = ttk.Frame(scrollable_frame)
        header_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Título principal
        title_label = ttk.Label(header_frame, text="WhatsApp Messenger Pro", 
                               font=("Helvetica", 18, "bold"))
        title_label.pack(pady=(0,10))
        
        subtitle_label = ttk.Label(header_frame, text="Envio de mensagens em massa com suporte internacional", 
                                 font=("Helvetica", 10), foreground="#555555")
        subtitle_label.pack()

        # Separador
        ttk.Separator(scrollable_frame, orient="horizontal").pack(fill=tk.X, padx=20, pady=10)

        # Status do servidor
        self.server_status_frame = ttk.LabelFrame(scrollable_frame, text="Status do Servidor", 
                                                padding=10, bootstyle=PRIMARY)
        self.server_status_frame.pack(fill=tk.X, padx=20, pady=5)
        
        status_container = ttk.Frame(self.server_status_frame)
        status_container.pack(fill=tk.X)
        
        self.status_text = tk.StringVar(value="Desconectado")
        
        # Ícone de status
        self.status_indicator = ttk.Label(status_container, text="●", font=("Helvetica", 16), 
                                        foreground="red")
        self.status_indicator.pack(side=tk.LEFT, padx=5)
        
        self.status_label = ttk.Label(status_container, textvariable=self.status_text, 
                                    font=("Helvetica", 11))
        self.status_label.pack(side=tk.LEFT, padx=5, pady=5)
        
        ttk.Button(status_container, text="Verificar Conexão", command=self.check_connection, 
                  bootstyle=INFO).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(status_container, text="Reiniciar Sessão", 
                  command=self.reset_whatsapp_session, 
                  bootstyle=WARNING).pack(side=tk.RIGHT, padx=5)
        
        # Frame para o QR Code
        self.qr_frame = ttk.LabelFrame(scrollable_frame, text="Escaneie o QR Code", 
                                     padding=10, bootstyle=WARNING)
        # Inicialmente oculto, será exibido se necessário
        
        qr_container = ttk.Frame(self.qr_frame)
        qr_container.pack(fill=tk.X)
        
        # Botão para obter QR code
        ttk.Button(qr_container, text="Obter QR Code", command=self.get_qr_code, 
                  bootstyle="warning").pack(pady=5)
        
        # Área de texto para QR code
        self.qr_text = scrolledtext.ScrolledText(self.qr_frame, height=10, width=50, 
                                               font=("Courier", 10), background="#f8f8f8", 
                                               foreground="#333")
        self.qr_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Separador
        ttk.Separator(scrollable_frame, orient="horizontal").pack(fill=tk.X, padx=20, pady=10)
        
        # NOVA ADIÇÃO: Área de mini logs para feedback do usuário
        self.log_frame = ttk.LabelFrame(scrollable_frame, text="Atividade Recente", 
                                      padding=10, bootstyle=INFO)
        self.log_frame.pack(fill=tk.X, padx=20, pady=5)
        
        # Cria uma área de texto rolável para os logs
        self.mini_log = scrolledtext.ScrolledText(self.log_frame, height=5, width=50, 
                                               font=("Consolas", 9), state="disabled",
                                               wrap="word")
        self.mini_log.pack(fill=tk.X, expand=True, pady=5)
        
        # Separador
        ttk.Separator(scrollable_frame, orient="horizontal").pack(fill=tk.X, padx=20, pady=10)
        
        # Cartões para importação de contatos e mensagem
        cards_container = ttk.Frame(scrollable_frame)
        cards_container.pack(fill=tk.X, padx=20, pady=5)
        
        # Cartão para importação de contatos
        contacts_card = ttk.LabelFrame(cards_container, text="Contatos", padding=15, bootstyle=SUCCESS)
        contacts_card.pack(fill=tk.X, pady=10)
        
        # Seleção do arquivo de contatos
        ttk.Label(contacts_card, text="Arquivo CSV/XLSX:", 
                 font=("Helvetica", 10, "bold")).pack(pady=5, anchor=tk.W)
        
        file_frame = ttk.Frame(contacts_card)
        file_frame.pack(fill=tk.X, pady=5)
        
        self.entry_file = ttk.Entry(file_frame)
        self.entry_file.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
        
        ttk.Button(file_frame, text="Selecionar", command=self.browse_file, 
                  bootstyle="success-outline").pack(side=tk.RIGHT)
        
        # Cartão para mensagem
        message_card = ttk.LabelFrame(cards_container, text="Mensagem", padding=15, bootstyle=INFO)
        message_card.pack(fill=tk.X, pady=10)
        
        # Campo para digitar a mensagem a ser enviada
        ttk.Label(message_card, text="Digite sua mensagem:", 
                 font=("Helvetica", 10, "bold")).pack(pady=5, anchor=tk.W)
        
        self.text_msg = tk.Text(message_card, height=5, width=50)
        self.text_msg.pack(fill=tk.X, pady=5)

        # Seleção de arquivos para anexar
        ttk.Label(message_card, text="Anexar Arquivos:", 
                 font=("Helvetica", 10, "bold")).pack(pady=5, anchor=tk.W)
        
        files_frame = ttk.Frame(message_card)
        files_frame.pack(fill=tk.X, pady=5)
        
        # Estilizando os botões
        ttk.Button(files_frame, text="Selecionar Arquivos", command=self.browse_attachment, 
                  bootstyle="info-outline").pack(side=tk.LEFT)
        
        # Lista de arquivos selecionados
        ttk.Label(message_card, text="Arquivos selecionados:", 
                 font=("Helvetica", 9)).pack(anchor=tk.W, pady=(10,5))
        
        self.files_listbox = ttk.Treeview(message_card, columns=("arquivo",), 
                                         show="headings", height=4)
        self.files_listbox.heading("arquivo", text="Nome do Arquivo")
        self.files_listbox.column("arquivo", width=100)
        self.files_listbox.pack(fill=tk.X, expand=True, pady=5)
        
        listbox_buttons = ttk.Frame(message_card)
        listbox_buttons.pack(fill=tk.X, pady=5)
        
        ttk.Button(listbox_buttons, text="Remover Selecionado", 
                  command=self.remove_selected_file, 
                  bootstyle="danger-outline").pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(listbox_buttons, text="Limpar Todos", 
                  command=self.clear_files, 
                  bootstyle="danger-outline").pack(side=tk.LEFT)
        
        self.files_list = []
        
        # Cartão para configurações
        settings_card = ttk.LabelFrame(scrollable_frame, text="Configurações de Envio", 
                                      padding=15, bootstyle=SECONDARY)
        settings_card.pack(fill=tk.X, padx=20, pady=10)
        
        settings_grid = ttk.Frame(settings_card)
        settings_grid.pack(fill=tk.X)
        
        # Intervalo entre mensagens
        ttk.Label(settings_grid, text="Intervalo entre mensagens (s):", 
                 font=("Helvetica", 10)).grid(row=0, column=0, sticky="w", padx=5, pady=8)
        self.interval_var = tk.IntVar(value=3)
        ttk.Spinbox(settings_grid, from_=1, to=60, textvariable=self.interval_var, 
                   width=5).grid(row=0, column=1, padx=5, pady=8)
        
        # Número de tentativas
        ttk.Label(settings_grid, text="Tentativas por mensagem:", 
                 font=("Helvetica", 10)).grid(row=1, column=0, sticky="w", padx=5, pady=8)
        self.retry_var = tk.IntVar(value=2)
        ttk.Spinbox(settings_grid, from_=1, to=5, textvariable=self.retry_var, 
                   width=5).grid(row=1, column=1, padx=5, pady=8)
        
        # Opção de variação de tempo
        self.random_interval_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_grid, text="Adicionar variação aleatória ao intervalo (1-3s)", 
                       variable=self.random_interval_var, 
                       bootstyle="round-toggle").grid(row=2, column=0, columnspan=2, 
                                                    sticky="w", padx=5, pady=8)

        # Cartão para controles de envio
        controls_card = ttk.Frame(scrollable_frame)
        controls_card.pack(fill=tk.X, padx=20, pady=10)
        
        # Botão para iniciar o envio
        ttk.Button(controls_card, text="Iniciar Envio", command=self.start_sending, 
                  bootstyle="success", width=20).pack(pady=10)

        # Barra de progresso
        progress_frame = ttk.Frame(controls_card)
        progress_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(progress_frame, text="Progresso:", 
                 font=("Helvetica", 10)).pack(anchor=tk.W)
        
        self.progress_bar = ttk.Progressbar(progress_frame, bootstyle="success-striped")
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        progress_info = ttk.Frame(progress_frame)
        progress_info.pack(fill=tk.X)
        
        self.progress_var = tk.StringVar(value="0 de 0")
        ttk.Label(progress_info, textvariable=self.progress_var).pack(side=tk.LEFT)
        
        self.estimated_var = tk.StringVar(value="00:00:00")
        ttk.Label(progress_info, text="Tempo Estimado:").pack(side=tk.RIGHT, padx=(0,5))
        ttk.Label(progress_info, textvariable=self.estimated_var).pack(side=tk.RIGHT)

        # Status detalhado
        status_detail = ttk.Frame(controls_card)
        status_detail.pack(fill=tk.X, pady=10)
        
        self.status_var = tk.StringVar(value="Pronto")
        status_label = ttk.Label(status_detail, text="Status:", font=("Helvetica", 10))
        status_label.pack(side=tk.LEFT)
        ttk.Label(status_detail, textvariable=self.status_var, 
                 font=("Helvetica", 10, "bold")).pack(side=tk.LEFT, padx=5)

        # Botão para parar o envio
        self.stop_button = ttk.Button(controls_card, text="Parar Envio", 
                                     command=self.stop_sending, 
                                     bootstyle="danger", state=tk.DISABLED)
        self.stop_button.pack(pady=5)

        # Frame para estatísticas (inicialmente oculto)
        self.stats_frame = ttk.LabelFrame(scrollable_frame, text="Estatísticas de Envio", 
                                        padding=15, bootstyle="info")
        # Inicialmente oculto, só será exibido após a conclusão do envio
        
        # Grid para exibir estatísticas
        stats_grid = ttk.Frame(self.stats_frame)
        stats_grid.pack(fill=tk.X, pady=5)
        
        # Cria as labels para estatísticas
        ttk.Label(stats_grid, text="Total de envios:", 
                 font=("Helvetica", 10)).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.total_var = tk.StringVar(value="0")
        ttk.Label(stats_grid, textvariable=self.total_var, 
                 font=("Helvetica", 10, "bold")).grid(row=0, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Label(stats_grid, text="Enviados com sucesso:", 
                 font=("Helvetica", 10)).grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.success_var = tk.StringVar(value="0")
        ttk.Label(stats_grid, textvariable=self.success_var, 
                 font=("Helvetica", 10, "bold"), 
                 foreground="#28a745").grid(row=1, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Label(stats_grid, text="Falhas no envio:", 
                 font=("Helvetica", 10)).grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.failures_var = tk.StringVar(value="0")
        ttk.Label(stats_grid, textvariable=self.failures_var, 
                 font=("Helvetica", 10, "bold"), 
                 foreground="#dc3545").grid(row=2, column=1, sticky="w", padx=5, pady=5)
        
        # Taxa de sucesso
        ttk.Label(stats_grid, text="Taxa de sucesso:", 
                 font=("Helvetica", 10)).grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.success_rate_var = tk.StringVar(value="0%")
        ttk.Label(stats_grid, textvariable=self.success_rate_var, 
                 font=("Helvetica", 10, "bold")).grid(row=3, column=1, sticky="w", padx=5, pady=5)
        
        # Botões para exportar falhas e ver detalhes
        stats_buttons = ttk.Frame(self.stats_frame)
        stats_buttons.pack(fill=tk.X, pady=10)
        
        ttk.Button(stats_buttons, text="Exportar Falhas para CSV", 
                  command=self.export_failed_numbers, 
                  bootstyle="warning").pack(side=tk.LEFT, padx=5)
        ttk.Button(stats_buttons, text="Ver Detalhes de Erros", 
                  command=self.show_error_details, 
                  bootstyle="info").pack(side=tk.LEFT, padx=5)

        # Adicionar rodapé
        footer_frame = ttk.Frame(scrollable_frame)
        footer_frame.pack(fill=tk.X, padx=20, pady=20)
        
        ttk.Separator(footer_frame, orient="horizontal").pack(fill=tk.X, pady=10)
        
        ttk.Label(footer_frame, text="WhatsApp Messenger Pro • v1.2.0", 
                 font=("Helvetica", 8), foreground="#888888").pack(side=tk.LEFT)
        
        # Inicializar variáveis
        self.contacts = []
        self.successful_numbers = []
        self.failed_numbers = []
        self.error_messages = {}
        self.running = False
        
        # Adiciona o primeiro log
        self.add_log("Sistema iniciado. Aguardando ações do usuário.")
        
        # Verificação automática da conexão
        self.check_connection_periodic()

    def on_window_resize(self, event=None):
        """Ajusta componentes quando a janela é redimensionada"""
        # Só tratamos redimensionamento da janela principal
        if event and event.widget == self.master:
            # Atualiza a largura dos componentes conforme necessário
            width = event.width - 40  # 40 pixels para margens esquerda e direita
            
            # Não fazemos nada se a largura for muito pequena
            if width < 100:
                return
                
            # Adiciona log informativo
            self.add_log(f"Janela redimensionada para {event.width}x{event.height}")

    def add_log(self, message, level="INFO"):
        """Adiciona uma mensagem ao mini log na interface"""
        # Define cores com base no nível de log
        color_map = {
            "INFO": "#000000",    # Preto
            "SUCCESS": "#28a745", # Verde
            "WARNING": "#ffc107", # Amarelo
            "ERROR": "#dc3545"    # Vermelho
        }
        color = color_map.get(level, "#000000")
        
        # Formata a mensagem com timestamp
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] [{level}] {message}\n"
        
        # Habilita a edição do widget de log
        self.mini_log.configure(state="normal")
        
        # Insere a mensagem com a cor apropriada
        self.mini_log.insert(tk.END, formatted_message)
        # Tentativa de configurar cor - pode não funcionar em todas as versões
        try:
            tag_name = f"tag_{timestamp.replace(':', '')}"
            self.mini_log.tag_add(tag_name, "end-1l", "end")
            self.mini_log.tag_config(tag_name, foreground=color)
        except Exception:
            # Se não conseguir configurar a cor, apenas insere o texto
            pass
        
        # Rola para o final para mostrar a mensagem mais recente
        self.mini_log.see(tk.END)
        
        # Desabilita a edição para evitar alterações pelo usuário
        self.mini_log.configure(state="disabled")
        
        # Também registra a mensagem no log do sistema se for algo importante
        if level in ["ERROR", "WARNING"]:
            self.log_to_file(message, level)

    def log_to_file(self, message, level):
        """Registra uma mensagem no arquivo de log"""
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"{timestamp} - {level}: {message}\n")

    def check_connection_periodic(self):
        """Verifica periodicamente a conexão com o servidor."""
        self.check_connection()
        # Agenda a próxima verificação em 30 segundos
        self.master.after(30000, self.check_connection_periodic)

    def check_connection(self):
        """Verifica a conexão com o servidor API."""
        self.add_log("Verificando conexão com o servidor...")
        
        try:
            response = requests.get(f"{API_BASE_URL}/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('ready', False):
                    self.status_text.set("Conectado e Pronto")
                    self.status_indicator.config(foreground="#28a745")  # Verde
                    self.add_log("Servidor conectado e autenticado com WhatsApp.", "SUCCESS")
                    # Esconde o QR code se já estiver conectado
                    self.qr_frame.pack_forget()
                else:
                    self.status_text.set("Aguardando Autenticação")
                    self.status_indicator.config(foreground="#ffc107")  # Amarelo
                    self.add_log("Servidor está online, mas aguardando autenticação no WhatsApp.", "WARNING")
                    # Mostra o frame QR Code apenas se não estiver pronto
                    if not self.qr_frame.winfo_ismapped():
                        self.qr_frame.pack(fill=tk.X, padx=20, pady=5, after=self.log_frame)
                    self.get_qr_code()  # Tenta obter o QR code automaticamente
            else:
                self.status_text.set(f"Erro: {response.status_code}")
                self.status_indicator.config(foreground="#dc3545")  # Vermelho
                self.add_log(f"Erro na comunicação com o servidor: Código {response.status_code}", "ERROR")
        except requests.RequestException as e:
            self.status_text.set(f"Erro de Conexão: Servidor Offline")
            self.status_indicator.config(foreground="#dc3545")  # Vermelho
            self.add_log(f"Servidor offline ou inacessível: {str(e)}", "ERROR")
            self.log_error(f"Erro de conexão com o servidor: {e}")

    def reset_whatsapp_session(self):
        """Reinicia a sessão do WhatsApp para gerar um novo QR code."""
        if messagebox.askyesno("Reiniciar Sessão", 
                              "Isso irá encerrar sua sessão atual do WhatsApp.\n\n"
                              "Você precisará escanear um novo QR code para reconectar.\n\n"
                              "Deseja continuar?"):
            try:
                self.add_log("Solicitando reinicialização da sessão do WhatsApp...")
                
                # Tenta fazer uma chamada à API para reiniciar a sessão
                response = requests.post(f"{API_BASE_URL}/reset-session", timeout=10)
                
                if response.status_code == 200:
                    self.add_log("Sessão do WhatsApp reiniciada com sucesso.", "SUCCESS")
                    self.status_text.set("Aguardando novo QR Code")
                    self.status_indicator.config(foreground="#ffc107")  # Amarelo
                    
                    # Exibe o frame do QR code se ainda não estiver visível
                    if not self.qr_frame.winfo_ismapped():
                        self.qr_frame.pack(fill=tk.X, padx=20, pady=5, after=self.log_frame)
                    
                    # Aguarda um momento e solicita o novo QR code
                    self.master.after(2000, self.get_qr_code)
                else:
                    error_msg = response.json().get('error', 'Erro desconhecido')
                    self.add_log(f"Erro ao reiniciar sessão: {error_msg}", "ERROR")
                    messagebox.showerror("Erro", f"Não foi possível reiniciar a sessão: {error_msg}")
            except Exception as e:
                self.add_log(f"Exceção ao reiniciar sessão: {str(e)}", "ERROR")
                messagebox.showerror("Erro", f"Ocorreu um erro ao reiniciar a sessão: {str(e)}")



    def get_qr_code(self):
        """Obtém e exibe o QR code do servidor."""
        self.add_log("Solicitando QR Code para autenticação...")
        
        try:
            response = requests.get(f"{API_BASE_URL}/qrcode", timeout=5)
            if response.status_code == 200:
                data = response.json()
                qr_code_text = data.get('qrCodeText')
                
                if qr_code_text:
                    # Limpa o texto anterior
                    self.qr_text.delete('1.0', tk.END)
                    # Insere o novo QR code
                    self.qr_text.insert(tk.END, qr_code_text)
                    self.add_log("QR Code recebido. Escaneie-o com seu WhatsApp.", "SUCCESS")
                else:
                    self.qr_text.delete('1.0', tk.END)
                    self.qr_text.insert(tk.END, "QR Code não disponível")
                    self.add_log("QR Code não disponível no momento.", "WARNING")
            else:
                self.qr_text.delete('1.0', tk.END)
                self.qr_text.insert(tk.END, f"Erro ao obter QR Code: {response.status_code}")
                self.add_log(f"Erro ao obter QR Code: Código {response.status_code}", "ERROR")
        except Exception as e:
            self.qr_text.delete('1.0', tk.END)
            self.qr_text.insert(tk.END, f"Erro: {str(e)}")
            self.add_log(f"Exceção ao obter QR code: {str(e)}", "ERROR")
            self.log_error(f"Erro ao obter QR code: {e}")

    def browse_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx")]
        )
        if file_path:
            self.entry_file.delete(0, tk.END)
            self.entry_file.insert(0, file_path)
            try:
                self.add_log(f"Carregando arquivo: {os.path.basename(file_path)}")
                
                if file_path.lower().endswith(".csv"):
                    df = pd.read_csv(file_path)
                elif file_path.lower().endswith(".xlsx"):
                    df = pd.read_excel(file_path)
                else:
                    messagebox.showerror("Erro", "Tipo de arquivo não suportado.")
                    self.add_log("Erro: Tipo de arquivo não suportado.", "ERROR")
                    return
                # Considera que os números estejam na primeira coluna
                self.contacts = df.iloc[:, 0].dropna().astype(str).tolist()
                
                self.add_log(f"{len(self.contacts)} contatos carregados com sucesso.", "SUCCESS")
                
                # Pergunta se o usuário deseja analisar os números
                if messagebox.askyesno("Análise de Números", f"{len(self.contacts)} contatos carregados. Deseja analisar os formatos dos números?"):
                    self.analyze_phone_numbers()
                
                self.progress_var.set(f"0 de {len(self.contacts)}")
                self.progress_bar["maximum"] = len(self.contacts)
                self.progress_bar["value"] = 0
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao ler o arquivo: {e}")
                self.add_log(f"Erro ao ler o arquivo: {str(e)}", "ERROR")

    def analyze_phone_numbers(self):
        """Analisa os números de telefone carregados e mostra informações de países."""
        if not self.contacts:
            messagebox.showerror("Erro", "Nenhum contato carregado.")
            self.add_log("Erro: Tentativa de análise sem contatos carregados", "ERROR")
            return
        
        try:
            self.add_log("Analisando formatos dos números de telefone...")
            
            # Envia os números para a API analisar
            response = requests.post(
                f"{API_BASE_URL}/analyze-batch",
                json={"numbers": self.contacts},
                timeout=10
            )
            
            if response.status_code != 200:
                messagebox.showerror("Erro", "Falha ao analisar números de telefone.")
                self.add_log("Erro na análise de números de telefone", "ERROR")
                return
                
            data = response.json()
            stats = data.get('stats', {})
            results = data.get('results', [])
            
            # Salva os resultados formatados para uso posterior
            self.contacts = [r.get('formattedNumber') for r in results]
            
            # Log estatísticas
            formatted_count = stats.get('formatted', 0)
            total_count = stats.get('total', 0)
            self.add_log(f"Análise concluída: {formatted_count} números de {total_count} têm formato reconhecido.", "SUCCESS")
            
            # Para cada país encontrado, registra no log
            for country, count in stats.get('byCountry', {}).items():
                self.add_log(f"Detectados {count} números do país: {country}")
            
            # Cria uma janela para mostrar os resultados
            analysis_window = ttk.Toplevel(self.master)
            analysis_window.title("Análise de Números de Telefone")
            analysis_window.geometry("700x500")
            
            # Frame para estatísticas
            stats_frame = ttk.LabelFrame(analysis_window, text="Estatísticas", padding=10, bootstyle=INFO)
            stats_frame.pack(fill=tk.X, padx=10, pady=5)
            
            # Exibe estatísticas gerais
            ttk.Label(stats_frame, text=f"Total de números: {stats.get('total', 0)}", 
                     font=("Helvetica", 10, "bold")).grid(row=0, column=0, sticky="w", padx=5, pady=2)
            ttk.Label(stats_frame, text=f"Números com formato reconhecido: {stats.get('formatted', 0)}", 
                     font=("Helvetica", 10)).grid(row=1, column=0, sticky="w", padx=5, pady=2)
            
            # Exibe estatísticas por país
            country_stats = stats.get('byCountry', {})
            ttk.Label(stats_frame, text="Distribuição por país:", 
                     font=("Helvetica", 10, "bold")).grid(row=2, column=0, sticky="w", padx=5, pady=(10,2))
            
            row = 3
            for country, count in country_stats.items():
                ttk.Label(stats_frame, text=f"• {country}: {count} números").grid(row=row, column=0, sticky="w", padx=20, pady=1)
                row += 1
            
            # Frame para lista de números
            numbers_frame = ttk.LabelFrame(analysis_window, text="Detalhes dos Números", padding=10, bootstyle=PRIMARY)
            numbers_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            # Cria uma tabela para mostrar os números
            cols = ("Número Original", "Número Formatado", "País", "Código")
            numbers_tree = ttk.Treeview(numbers_frame, columns=cols, show='headings', bootstyle=INFO)
            
            # Define as colunas da tabela
            for col in cols:
                numbers_tree.heading(col, text=col)
                numbers_tree.column(col, width=100)
            
            # Adiciona uma scrollbar
            scrollbar = ttk.Scrollbar(numbers_frame, orient="vertical", command=numbers_tree.yview)
            numbers_tree.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side="right", fill="y")
            numbers_tree.pack(side="left", fill="both", expand=True)
            
            # Preenche a tabela com os números
            for result in results:
                country_info = result.get('countryInfo', {})
                numbers_tree.insert("", "end", values=(
                    result.get('original', ''),
                    result.get('formattedNumber', ''),
                    country_info.get('country', 'Desconhecido'),
                    country_info.get('code', '')
                ))
            
            # Botões de ação
            buttons_frame = ttk.Frame(analysis_window)
            buttons_frame.pack(fill=tk.X, padx=10, pady=10)
            
            ttk.Button(
                buttons_frame, 
                text="Usar Números Formatados", 
                command=lambda: [
                    analysis_window.destroy(), 
                    messagebox.showinfo("Números Atualizados", f"{len(self.contacts)} números foram formatados para uso internacional."),
                    self.add_log("Números formatados aplicados à lista de envio.", "SUCCESS")
                ],
                bootstyle=SUCCESS
            ).pack(side=tk.LEFT, padx=5)
            
            ttk.Button(
                buttons_frame, 
                text="Cancelar", 
                command=lambda: [
                    analysis_window.destroy(),
                    self.add_log("Análise de números cancelada pelo usuário.")
                ],
                bootstyle=SECONDARY
            ).pack(side=tk.RIGHT, padx=5)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro na análise de números: {e}")
            self.add_log(f"Exceção durante análise de números: {str(e)}", "ERROR")

    def browse_attachment(self):
        file_paths = filedialog.askopenfilenames(
            title="Selecione os arquivos para anexar"
        )
        if file_paths:
            for file_path in file_paths:
                if file_path not in self.files_list:
                    self.files_list.append(file_path)
                    filename = os.path.basename(file_path)
                    self.files_listbox.insert("", "end", values=(filename,))
                    self.add_log(f"Arquivo anexado: {filename}")
            
            self.add_log(f"Total de {len(self.files_list)} arquivos anexados.", "SUCCESS")

    def remove_selected_file(self):
        try:
            selected_item = self.files_listbox.selection()[0]
            selected_index = self.files_listbox.index(selected_item)
            file_path = self.files_list[selected_index]
            filename = os.path.basename(file_path)
            
            self.files_list.pop(selected_index)
            self.files_listbox.delete(selected_item)
            
            self.add_log(f"Arquivo removido: {filename}")
        except (IndexError, Exception) as e:
            self.add_log("Erro ao remover arquivo: Nenhum arquivo selecionado", "WARNING")

    def clear_files(self):
        count = len(self.files_list)
        self.files_list = []
        for item in self.files_listbox.get_children():
            self.files_listbox.delete(item)
        
        self.add_log(f"{count} arquivos removidos da lista.")

    def start_sending(self):
        if not self.contacts:
            messagebox.showerror("Erro", "Nenhum contato carregado.")
            self.add_log("Erro: Tentativa de envio sem contatos carregados", "ERROR")
            return
        
        # Verifica a conexão com o servidor
        try:
            self.add_log("Verificando estado do servidor antes do envio...")
            
            response = requests.get(f"{API_BASE_URL}/status", timeout=5)
            if response.status_code != 200 or not response.json().get('ready', False):
                messagebox.showerror("Erro", "Servidor não está pronto. Verifique a conexão e autenticação.")
                self.add_log("Erro: Servidor não está pronto para envio de mensagens", "ERROR")
                return
        except requests.RequestException as e:
            messagebox.showerror("Erro", "Não foi possível conectar ao servidor. Verifique se o servidor está rodando.")
            self.add_log(f"Erro de conexão com o servidor: {str(e)}", "ERROR")
            return
        
        msg_text = self.text_msg.get("1.0", tk.END).strip()
        if not msg_text and not self.files_list:
            messagebox.showerror("Erro", "Digite uma mensagem ou selecione pelo menos um arquivo.")
            self.add_log("Erro: Tentativa de envio sem mensagem ou anexos", "ERROR")
            return
        
        self.add_log(f"Iniciando envio para {len(self.contacts)} contatos...", "SUCCESS")
        if msg_text:
            self.add_log("Tipo de envio: Mensagem de texto")
        if self.files_list:
            self.add_log(f"Tipo de envio: {len(self.files_list)} arquivos anexados")
        
        self.running = True
        self.stop_button["state"] = tk.NORMAL
        # Inicia o envio em uma thread para evitar travar a interface
        threading.Thread(target=self.send_messages, args=(msg_text,), daemon=True).start()

    def stop_sending(self):
        self.running = False
        self.status_var.set("Parando processo...")
        self.stop_button["state"] = tk.DISABLED
        self.add_log("Interrupção do processo de envio solicitada pelo usuário", "WARNING")

    def update_statistics(self):
        """Atualiza os valores das estatísticas na interface."""
        total = len(self.contacts)
        success = len(self.successful_numbers)
        failures = len(self.failed_numbers)
        
        self.total_var.set(str(total))
        self.success_var.set(str(success))
        self.failures_var.set(str(failures))
        
        # Calcula taxa de sucesso
        if total > 0:
            success_rate = (success / (success + failures)) * 100 if success + failures > 0 else 0
            self.success_rate_var.set(f"{success_rate:.1f}%")
        else:
            self.success_rate_var.set("0%")

    def show_error_details(self):
        """Exibe uma janela com detalhes dos erros ocorridos durante o envio."""
        if not self.error_messages:
            messagebox.showinfo("Detalhes de Erros", "Não há erros para mostrar.")
            self.add_log("Solicitação de detalhes de erros: Nenhum erro registrado.")
            return
            
        self.add_log(f"Exibindo detalhes de {len(self.error_messages)} erros.")
            
        # Cria uma nova janela para mostrar os erros
        error_window = ttk.Toplevel(self.master)
        error_window.title("Detalhes dos Erros")
        error_window.geometry("700x500")
        
        # Título e descrição
        ttk.Label(error_window, text="Detalhes dos Erros de Envio", 
                 font=("Helvetica", 14, "bold")).pack(padx=10, pady=(10,5))
        ttk.Label(error_window, text=f"Total de {len(self.error_messages)} erros encontrados", 
                 font=("Helvetica", 10)).pack(padx=10, pady=(0,10))
        
        # Cria um Treeview para mostrar os erros de forma mais organizada
        columns = ("Número", "Erro")
        error_tree = ttk.Treeview(error_window, columns=columns, show="headings", bootstyle=DANGER)
        
        # Configura as colunas
        error_tree.heading("Número", text="Número")
        error_tree.heading("Erro", text="Mensagem de Erro")
        error_tree.column("Número", width=150)
        error_tree.column("Erro", width=500)
        
        # Adiciona scrollbar
        tree_scroll = ttk.Scrollbar(error_window, orient="vertical", command=error_tree.yview)
        error_tree.configure(yscrollcommand=tree_scroll.set)
        
        # Empacota os elementos
        tree_scroll.pack(side="right", fill="y")
        error_tree.pack(padx=10, pady=10, fill="both", expand=True)
        
        # Preenche a tabela com os erros
        for number, error in self.error_messages.items():
            error_tree.insert("", "end", values=(number, error))
        
        # Botão para fechar a janela
        ttk.Button(error_window, text="Fechar", 
                 command=lambda: [error_window.destroy(), self.add_log("Janela de detalhes de erros fechada.")], 
                 bootstyle=SECONDARY, width=20).pack(pady=10)

    def export_failed_numbers(self):
        """Exporta os números que falharam durante o envio para um arquivo CSV."""
        if not self.failed_numbers:
            messagebox.showinfo("Exportar Falhas", "Não há falhas para exportar.")
            self.add_log("Solicitação de exportação de falhas: Nenhuma falha registrada.")
            return
        
        self.add_log(f"Preparando exportação de {len(self.failed_numbers)} números com falha...")
        
        try:
            # Solicita onde salvar o arquivo
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                title="Salvar números com falha como"
            )
            
            if not file_path:  # Usuário cancelou
                self.add_log("Exportação de falhas cancelada pelo usuário.")
                return
                
            # Cria o DataFrame com os números e erros
            data = []
            for number in self.failed_numbers:
                error_message = self.error_messages.get(number, "Erro desconhecido")
                data.append({"Número": number, "Erro": error_message})
            
            df = pd.DataFrame(data)
            
            # Salva o DataFrame como CSV
            df.to_csv(file_path, index=False, encoding='utf-8')
            
            self.add_log(f"Números com falha exportados para: {os.path.basename(file_path)}", "SUCCESS")
            messagebox.showinfo("Exportar Falhas", f"Arquivo salvo com sucesso em:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar falhas: {e}")
            self.add_log(f"Erro ao exportar falhas: {str(e)}", "ERROR")

    def send_messages(self, msg_text):
        """Envia mensagens para todos os contatos usando a API."""
        # Limpa os dados anteriores
        self.successful_numbers = []
        self.failed_numbers = []
        self.error_messages = {}
        
        total_contacts = len(self.contacts)
        times = []
        self.progress_bar["value"] = 0

        for idx, number in enumerate(self.contacts, start=1):
            if not self.running:
                self.status_var.set("Envio interrompido")
                self.add_log("Processo de envio interrompido pelo usuário.", "WARNING")
                break
                
            start_time = time.time()
            self.status_var.set(f"Enviando para contato {idx}/{total_contacts}...")
            self.add_log(f"Processando contato {idx}/{total_contacts}: {number}")

            # Tenta enviar a mensagem com número de tentativas configurado
            success = False
            attempt = 0
            max_attempts = self.retry_var.get()
            last_error = ""
            
            while not success and attempt < max_attempts and self.running:
                attempt += 1
                if attempt > 1:
                    self.status_var.set(f"Tentativa {attempt}/{max_attempts} para contato {idx}...")
                    self.add_log(f"Tentativa {attempt}/{max_attempts} para o número {number}")
                
                # Envia a mensagem de texto (se houver)
                if msg_text:
                    text_success, text_error = self.send_text_message(number, msg_text)
                    if not text_success:
                        last_error = text_error
                        self.add_log(f"Falha ao enviar texto para {number}: {text_error}", "ERROR")
                else:
                    text_success = True  # Se não há mensagem, considera como sucesso
                
                # Envia os arquivos (se houver)
                files_success = True
                files_error = ""
                if self.files_list:
                    for file_path in self.files_list:
                        filename = os.path.basename(file_path)
                        self.add_log(f"Enviando arquivo: {filename} para {number}")
                        file_success, file_error = self.send_file(number, file_path)
                        if not file_success:
                            files_success = False
                            last_error = file_error
                            self.add_log(f"Falha ao enviar arquivo {filename}: {file_error}", "ERROR")
                            break
                
                success = text_success and files_success
                
                if success:
                    self.add_log(f"Mensagem enviada com sucesso para {number}", "SUCCESS")
                elif attempt < max_attempts:
                    # Espera um pouco antes de tentar novamente
                    self.add_log(f"Aguardando 2s para nova tentativa...", "WARNING")
                    time.sleep(2)
            
            # Registra o resultado
            if success:
                self.successful_numbers.append(number)
                self.log_success(f"Mensagem enviada para: {number}")
            else:
                self.failed_numbers.append(number)
                self.error_messages[number] = last_error
                self.log_error(f"Falha ao enviar para: {number} - Erro: {last_error}")

            # Atualiza estatísticas em tempo real
            self.update_statistics()

            # Calcula tempo e atualiza a interface
            elapsed = time.time() - start_time
            times.append(elapsed)
            avg_time = sum(times) / len(times)
            remaining = total_contacts - idx
            estimated_remaining = avg_time * remaining
            
            # Atualiza a interface com o progresso e tempo estimado
            self.progress_var.set(f"{idx} de {total_contacts}")
            self.estimated_var.set(str(datetime.timedelta(seconds=int(estimated_remaining))))
            self.progress_bar["value"] = idx

            # Determina o tempo de espera entre mensagens
            interval = self.interval_var.get()
            if self.random_interval_var.get():
                random_interval = random.randint(1, 3)
                interval += random_interval
                self.add_log(f"Adicionado intervalo aleatório de {random_interval}s")
                
            # Aguarda antes de enviar a próxima mensagem
            if idx < total_contacts:  # Não espera após o último contato
                self.status_var.set(f"Aguardando {interval}s antes da próxima mensagem...")
                self.add_log(f"Aguardando {interval}s antes do próximo envio...")
                for i in range(interval):
                    if not self.running:
                        break
                    time.sleep(1)
        
        # Após finalizar, mostra o frame de estatísticas
        if not self.stats_frame.winfo_ismapped():
            self.stats_frame.pack(fill=tk.X, padx=20, pady=5, after=self.stop_button)

        if self.running:  # Somente mostra mensagem se não foi interrompido
            self.status_var.set("Envio concluído")
            self.add_log(f"Processo concluído. Sucesso: {len(self.successful_numbers)}, Falhas: {len(self.failed_numbers)}", "SUCCESS")
            messagebox.showinfo("Concluído", f"Envio de mensagens concluído.\nSucesso: {len(self.successful_numbers)}\nFalhas: {len(self.failed_numbers)}")
        
        self.running = False
        self.stop_button["state"] = tk.DISABLED

    def send_text_message(self, number, message):
        """Envia uma mensagem de texto para um número usando a API."""
        try:
            response = requests.post(
                f"{API_BASE_URL}/send-message",
                json={"number": number, "message": message},
                timeout=30
            )
            
            if response.status_code == 200:
                return True, ""
            else:
                error_msg = response.json().get('error', 'Erro desconhecido')
                self.log_error(f"Erro API (texto): {error_msg}")
                return False, error_msg
        except Exception as e:
            error_msg = str(e)
            self.log_error(f"Exceção ao enviar texto: {error_msg}")
            return False, error_msg

    def send_file(self, number, file_path):
        """Envia um arquivo para um número usando a API."""
        try:
            with open(file_path, 'rb') as file:
                filename = os.path.basename(file_path)
                files = {'file': (filename, file)}
                data = {'number': number}
                
                response = requests.post(
                    f"{API_BASE_URL}/send-file",
                    data=data,
                    files=files,
                    timeout=60  # Timeout maior para upload de arquivos
                )
                
                if response.status_code == 200:
                    return True, ""
                else:
                    error_msg = response.json().get('error', 'Erro desconhecido')
                    self.log_error(f"Erro API (arquivo): {error_msg}")
                    return False, error_msg
        except Exception as e:
            error_msg = str(e)
            self.log_error(f"Exceção ao enviar arquivo: {error_msg}")
            return False, error_msg

    def log_success(self, message):
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{datetime.datetime.now()} - SUCESSO: {message}\n")
    
    def log_error(self, message):
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{datetime.datetime.now()} - ERRO: {message}\n")
    
    def log_warning(self, message):
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{datetime.datetime.now()} - AVISO: {message}\n")


if __name__ == '__main__':
    # Cria a aplicação com tema moderno
    root = ttk.Window(themename="litera")
    root.title("WhatsApp Messenger Pro")
    
    # Definir um ícone para a aplicação (opcional)
    # root.iconbitmap('path_to_icon.ico')  # No Windows
    
    app = WhatsAppMessengerGUI(root)
    root.mainloop()