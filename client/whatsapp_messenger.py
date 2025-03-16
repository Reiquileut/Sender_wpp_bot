import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext
import pandas as pd
import time
import datetime
import threading
import os
import requests
import json
import random
import csv

# Nome do arquivo de log
LOG_FILE = "log.txt"
# URL base da API (ajuste conforme necessário)
API_BASE_URL = "http://localhost:3000/api"

class WhatsAppMessengerGUI:
    def __init__(self, master):
        self.master = master
        master.title("WhatsApp Messenger")
        master.geometry("700x750")

        # Frame principal com scrollbar
        main_frame = tk.Frame(master)
        main_frame.pack(fill=tk.BOTH, expand=1)
        
        # Canvas e scrollbar
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Status do servidor
        self.server_status_frame = tk.LabelFrame(scrollable_frame, text="Status do Servidor")
        self.server_status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.status_text = tk.StringVar(value="Desconectado")
        self.status_label = tk.Label(self.server_status_frame, textvariable=self.status_text, fg="red")
        self.status_label.pack(side=tk.LEFT, padx=5, pady=5)
        
        tk.Button(self.server_status_frame, text="Verificar Conexão", command=self.check_connection).pack(side=tk.RIGHT, padx=5, pady=5)
        
        # Frame para o QR Code
        self.qr_frame = tk.LabelFrame(scrollable_frame, text="Escaneie o QR Code")
        # Inicialmente oculto, será exibido se necessário
        
        # Botão para obter QR code
        tk.Button(self.qr_frame, text="Obter QR Code", command=self.get_qr_code).pack(pady=5)
        
        # Área de texto para QR code
        self.qr_text = scrolledtext.ScrolledText(self.qr_frame, height=10, width=50, font=("Courier", 10))
        self.qr_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Seleção do arquivo de contatos
        tk.Label(scrollable_frame, text="Arquivo CSV/XLSX:").pack(pady=5)
        file_frame = tk.Frame(scrollable_frame)
        file_frame.pack(fill=tk.X, padx=10)
        
        self.entry_file = tk.Entry(file_frame, width=50)
        self.entry_file.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Button(file_frame, text="Selecionar", command=self.browse_file).pack(side=tk.RIGHT, padx=5)

        # Campo para digitar a mensagem a ser enviada
        tk.Label(scrollable_frame, text="Mensagem:").pack(pady=5)
        self.text_msg = tk.Text(scrollable_frame, height=5, width=50)
        self.text_msg.pack(padx=10, fill=tk.X)

        # Seleção de arquivos para anexar
        tk.Label(scrollable_frame, text="Anexar Arquivos:").pack(pady=5)
        files_frame = tk.Frame(scrollable_frame)
        files_frame.pack(fill=tk.X, padx=10)
        
        self.entry_attachment = tk.Entry(files_frame, width=50, state="readonly")
        self.entry_attachment.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Button(files_frame, text="Selecionar", command=self.browse_attachment).pack(side=tk.RIGHT, padx=5)

        # Lista de arquivos selecionados
        self.files_listbox_frame = tk.Frame(scrollable_frame)
        self.files_listbox_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(self.files_listbox_frame, text="Arquivos selecionados:").pack(anchor="w")
        self.files_listbox = tk.Listbox(self.files_listbox_frame, height=4)
        self.files_listbox.pack(fill=tk.X, expand=True)
        
        listbox_buttons = tk.Frame(self.files_listbox_frame)
        listbox_buttons.pack(fill=tk.X)
        tk.Button(listbox_buttons, text="Remover Selecionado", command=self.remove_selected_file).pack(side=tk.LEFT, padx=5)
        tk.Button(listbox_buttons, text="Limpar Todos", command=self.clear_files).pack(side=tk.LEFT)
        
        self.files_list = []
        
        # Configurações de envio
        settings_frame = tk.LabelFrame(scrollable_frame, text="Configurações")
        settings_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Intervalo entre mensagens
        tk.Label(settings_frame, text="Intervalo entre mensagens (s):").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.interval_var = tk.IntVar(value=3)
        tk.Spinbox(settings_frame, from_=1, to=60, textvariable=self.interval_var, width=5).grid(row=0, column=1, padx=5, pady=5)
        
        # Número de tentativas
        tk.Label(settings_frame, text="Tentativas por mensagem:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.retry_var = tk.IntVar(value=2)
        tk.Spinbox(settings_frame, from_=1, to=5, textvariable=self.retry_var, width=5).grid(row=1, column=1, padx=5, pady=5)
        
        # Opção de variação de tempo
        self.random_interval_var = tk.BooleanVar(value=True)
        tk.Checkbutton(settings_frame, text="Adicionar variação aleatória ao intervalo (1-3s)", 
                     variable=self.random_interval_var).grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=5)

        # Botão para iniciar o envio
        tk.Button(scrollable_frame, text="Iniciar Envio", command=self.start_sending, 
                 bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), pady=5).pack(pady=10)

        # Barra de progresso
        tk.Label(scrollable_frame, text="Progresso:").pack()
        self.progress_bar = ttk.Progressbar(scrollable_frame, orient="horizontal", length=400, mode="determinate")
        self.progress_bar.pack(pady=5)
        
        self.progress_var = tk.StringVar(value="0 de 0")
        tk.Label(scrollable_frame, textvariable=self.progress_var).pack()

        # Status e tempo estimado
        status_detail_frame = tk.Frame(scrollable_frame)
        status_detail_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(status_detail_frame, text="Status:").grid(row=0, column=0, sticky="w")
        self.status_var = tk.StringVar(value="Pronto")
        tk.Label(status_detail_frame, textvariable=self.status_var, width=30, anchor="w").grid(row=0, column=1, sticky="w")
        
        tk.Label(status_detail_frame, text="Tempo Estimado:").grid(row=1, column=0, sticky="w")
        self.estimated_var = tk.StringVar(value="00:00:00")
        tk.Label(status_detail_frame, textvariable=self.estimated_var).grid(row=1, column=1, sticky="w")

        # Botão para parar o envio
        self.stop_button = tk.Button(scrollable_frame, text="Parar Envio", command=self.stop_sending, 
                                   bg="#f44336", fg="white", state=tk.DISABLED)
        self.stop_button.pack(pady=5)

        # Adicionar variáveis para rastreamento de erros
        self.successful_numbers = []
        self.failed_numbers = []
        self.error_messages = {}  # Dicionário para armazenar {número: mensagem de erro}
        
        # Frame para estatísticas (inicialmente oculto)
        self.stats_frame = tk.LabelFrame(scrollable_frame, text="Estatísticas de Envio")
        # Inicialmente oculto, só será exibido após a conclusão do envio
        
        # Labels para exibir estatísticas
        self.stats_labels_frame = tk.Frame(self.stats_frame)
        self.stats_labels_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Cria as labels para estatísticas
        tk.Label(self.stats_labels_frame, text="Total de envios:").grid(row=0, column=0, sticky="w")
        self.total_var = tk.StringVar(value="0")
        tk.Label(self.stats_labels_frame, textvariable=self.total_var).grid(row=0, column=1, sticky="w")
        
        tk.Label(self.stats_labels_frame, text="Enviados com sucesso:").grid(row=1, column=0, sticky="w")
        self.success_var = tk.StringVar(value="0")
        tk.Label(self.stats_labels_frame, textvariable=self.success_var, fg="green").grid(row=1, column=1, sticky="w")
        
        tk.Label(self.stats_labels_frame, text="Falhas no envio:").grid(row=2, column=0, sticky="w")
        self.failures_var = tk.StringVar(value="0")
        tk.Label(self.stats_labels_frame, textvariable=self.failures_var, fg="red").grid(row=2, column=1, sticky="w")
        
        # Botões para exportar falhas e ver detalhes
        self.stats_buttons_frame = tk.Frame(self.stats_frame)
        self.stats_buttons_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(self.stats_buttons_frame, text="Exportar Falhas para CSV", 
                  command=self.export_failed_numbers).pack(side=tk.LEFT, padx=5)
        tk.Button(self.stats_buttons_frame, text="Ver Detalhes de Erros", 
                  command=self.show_error_details).pack(side=tk.LEFT, padx=5)

        self.contacts = []
        self.running = False
        
        # Verificação automática da conexão
        self.check_connection_periodic()

    def check_connection_periodic(self):
        """Verifica periodicamente a conexão com o servidor."""
        self.check_connection()
        # Agenda a próxima verificação em 30 segundos
        self.master.after(30000, self.check_connection_periodic)

    def check_connection(self):
        """Verifica a conexão com o servidor API."""
        try:
            response = requests.get(f"{API_BASE_URL}/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('ready', False):
                    self.status_text.set("Conectado e Pronto")
                    self.status_label.config(fg="green")
                    # Esconde o QR code se já estiver conectado
                    self.qr_frame.pack_forget()
                else:
                    self.status_text.set("Aguardando Autenticação")
                    self.status_label.config(fg="orange")
                    # Mostra o frame QR Code apenas se não estiver pronto
                    if not self.qr_frame.winfo_ismapped():
                        self.qr_frame.pack(fill=tk.X, padx=10, pady=5, after=self.server_status_frame)
                    self.get_qr_code()  # Tenta obter o QR code automaticamente
            else:
                self.status_text.set(f"Erro: {response.status_code}")
                self.status_label.config(fg="red")
        except requests.RequestException as e:
            self.status_text.set(f"Erro de Conexão: Servidor Offline")
            self.status_label.config(fg="red")
            self.log_error(f"Erro de conexão com o servidor: {e}")

    def get_qr_code(self):
        """Obtém e exibe o QR code do servidor."""
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
                else:
                    self.qr_text.delete('1.0', tk.END)
                    self.qr_text.insert(tk.END, "QR Code não disponível")
            else:
                self.qr_text.delete('1.0', tk.END)
                self.qr_text.insert(tk.END, f"Erro ao obter QR Code: {response.status_code}")
        except Exception as e:
            self.qr_text.delete('1.0', tk.END)
            self.qr_text.insert(tk.END, f"Erro: {str(e)}")
            self.log_error(f"Erro ao obter QR code: {e}")

    def browse_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx")]
        )
        if file_path:
            self.entry_file.delete(0, tk.END)
            self.entry_file.insert(0, file_path)
            try:
                if file_path.lower().endswith(".csv"):
                    df = pd.read_csv(file_path)
                elif file_path.lower().endswith(".xlsx"):
                    df = pd.read_excel(file_path)
                else:
                    messagebox.showerror("Erro", "Tipo de arquivo não suportado.")
                    return
                # Considera que os números estejam na primeira coluna
                self.contacts = df.iloc[:, 0].dropna().astype(str).tolist()
                
                # Pergunta se o usuário deseja analisar os números
                if messagebox.askyesno("Análise de Números", f"{len(self.contacts)} contatos carregados. Deseja analisar os formatos dos números?"):
                    self.analyze_phone_numbers()
                
                self.progress_var.set(f"0 de {len(self.contacts)}")
                self.progress_bar["maximum"] = len(self.contacts)
                self.progress_bar["value"] = 0
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao ler o arquivo: {e}")

    def analyze_phone_numbers(self):
        """Analisa os números de telefone carregados e mostra informações de países."""
        if not self.contacts:
            messagebox.showerror("Erro", "Nenhum contato carregado.")
            return
        
        try:
            # Envia os números para a API analisar
            response = requests.post(
                f"{API_BASE_URL}/analyze-batch",
                json={"numbers": self.contacts},
                timeout=10
            )
            
            if response.status_code != 200:
                messagebox.showerror("Erro", "Falha ao analisar números de telefone.")
                return
                
            data = response.json()
            stats = data.get('stats', {})
            results = data.get('results', [])
            
            # Salva os resultados formatados para uso posterior
            self.contacts = [r.get('formattedNumber') for r in results]
            
            # Cria uma janela para mostrar os resultados
            analysis_window = tk.Toplevel(self.master)
            analysis_window.title("Análise de Números de Telefone")
            analysis_window.geometry("700x500")
            
            # Frame para estatísticas
            stats_frame = tk.LabelFrame(analysis_window, text="Estatísticas")
            stats_frame.pack(fill=tk.X, padx=10, pady=5)
            
            # Exibe estatísticas gerais
            tk.Label(stats_frame, text=f"Total de números: {stats.get('total', 0)}").grid(row=0, column=0, sticky="w", padx=5, pady=2)
            tk.Label(stats_frame, text=f"Números com formato reconhecido: {stats.get('formatted', 0)}").grid(row=1, column=0, sticky="w", padx=5, pady=2)
            
            # Exibe estatísticas por país
            country_stats = stats.get('byCountry', {})
            tk.Label(stats_frame, text="Distribuição por país:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
            
            row = 3
            for country, count in country_stats.items():
                tk.Label(stats_frame, text=f"{country}: {count} números").grid(row=row, column=0, sticky="w", padx=20, pady=1)
                row += 1
            
            # Frame para lista de números
            numbers_frame = tk.LabelFrame(analysis_window, text="Detalhes dos Números")
            numbers_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            # Cria uma tabela para mostrar os números
            cols = ("Número Original", "Número Formatado", "País", "Código")
            numbers_tree = ttk.Treeview(numbers_frame, columns=cols, show='headings')
            
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
            buttons_frame = tk.Frame(analysis_window)
            buttons_frame.pack(fill=tk.X, padx=10, pady=10)
            
            tk.Button(
                buttons_frame, 
                text="Usar Números Formatados", 
                command=lambda: [analysis_window.destroy(), messagebox.showinfo("Números Atualizados", f"{len(self.contacts)} números foram formatados para uso internacional.")]
            ).pack(side=tk.LEFT, padx=5)
            
            tk.Button(
                buttons_frame, 
                text="Cancelar", 
                command=analysis_window.destroy
            ).pack(side=tk.RIGHT, padx=5)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro na análise de números: {e}")

    def browse_attachment(self):
        file_paths = filedialog.askopenfilenames(
            title="Selecione os arquivos para anexar"
        )
        if file_paths:
            for file_path in file_paths:
                if file_path not in self.files_list:
                    self.files_list.append(file_path)
                    filename = os.path.basename(file_path)
                    self.files_listbox.insert(tk.END, filename)

    def remove_selected_file(self):
        try:
            selected_index = self.files_listbox.curselection()[0]
            file_path = self.files_list[selected_index]
            self.files_list.pop(selected_index)
            self.files_listbox.delete(selected_index)
        except (IndexError, Exception):
            pass

    def clear_files(self):
        self.files_list = []
        self.files_listbox.delete(0, tk.END)

    def start_sending(self):
        if not self.contacts:
            messagebox.showerror("Erro", "Nenhum contato carregado.")
            return
        
        # Verifica a conexão com o servidor
        try:
            response = requests.get(f"{API_BASE_URL}/status", timeout=5)
            if response.status_code != 200 or not response.json().get('ready', False):
                messagebox.showerror("Erro", "Servidor não está pronto. Verifique a conexão e autenticação.")
                return
        except requests.RequestException:
            messagebox.showerror("Erro", "Não foi possível conectar ao servidor. Verifique se o servidor está rodando.")
            return
        
        msg_text = self.text_msg.get("1.0", tk.END).strip()
        if not msg_text and not self.files_list:
            messagebox.showerror("Erro", "Digite uma mensagem ou selecione pelo menos um arquivo.")
            return
            
        self.running = True
        self.stop_button["state"] = tk.NORMAL
        # Inicia o envio em uma thread para evitar travar a interface
        threading.Thread(target=self.send_messages, args=(msg_text,), daemon=True).start()

    def stop_sending(self):
        self.running = False
        self.status_var.set("Parando processo...")
        self.stop_button["state"] = tk.DISABLED

    def update_statistics(self):
        """Atualiza os valores das estatísticas na interface."""
        total = len(self.contacts)
        success = len(self.successful_numbers)
        failures = len(self.failed_numbers)
        
        self.total_var.set(str(total))
        self.success_var.set(str(success))
        self.failures_var.set(str(failures))

    def show_error_details(self):
        """Exibe uma janela com detalhes dos erros ocorridos durante o envio."""
        if not self.error_messages:
            messagebox.showinfo("Detalhes de Erros", "Não há erros para mostrar.")
            return
            
        # Cria uma nova janela para mostrar os erros
        error_window = tk.Toplevel(self.master)
        error_window.title("Detalhes dos Erros")
        error_window.geometry("600x400")
        
        # Cria um widget de texto com rolagem
        error_text = scrolledtext.ScrolledText(error_window, width=70, height=20)
        error_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # Adiciona os erros ao widget de texto
        error_text.insert(tk.END, "NÚMERO | ERRO\n")
        error_text.insert(tk.END, "-" * 60 + "\n")
        
        for number, error in self.error_messages.items():
            error_text.insert(tk.END, f"{number} | {error}\n")
        
        # Botão para fechar a janela
        tk.Button(error_window, text="Fechar", command=error_window.destroy).pack(pady=10)

    def export_failed_numbers(self):
        """Exporta os números que falharam durante o envio para um arquivo CSV."""
        if not self.failed_numbers:
            messagebox.showinfo("Exportar Falhas", "Não há falhas para exportar.")
            return
        
        try:
            # Solicita onde salvar o arquivo
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                title="Salvar números com falha como"
            )
            
            if not file_path:  # Usuário cancelou
                return
                
            # Cria o DataFrame com os números e erros
            data = []
            for number in self.failed_numbers:
                error_message = self.error_messages.get(number, "Erro desconhecido")
                data.append({"Número": number, "Erro": error_message})
            
            df = pd.DataFrame(data)
            
            # Salva o DataFrame como CSV
            df.to_csv(file_path, index=False, encoding='utf-8')
            
            messagebox.showinfo("Exportar Falhas", f"Arquivo salvo com sucesso em:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar falhas: {e}")

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
                break
                
            start_time = time.time()
            self.status_var.set(f"Enviando para contato {idx}/{total_contacts}...")

            # Tenta enviar a mensagem com número de tentativas configurado
            success = False
            attempt = 0
            max_attempts = self.retry_var.get()
            last_error = ""
            
            while not success and attempt < max_attempts and self.running:
                attempt += 1
                if attempt > 1:
                    self.status_var.set(f"Tentativa {attempt}/{max_attempts} para contato {idx}...")
                
                # Envia a mensagem de texto (se houver)
                if msg_text:
                    text_success, text_error = self.send_text_message(number, msg_text)
                    if not text_success:
                        last_error = text_error
                else:
                    text_success = True  # Se não há mensagem, considera como sucesso
                
                # Envia os arquivos (se houver)
                files_success = True
                files_error = ""
                if self.files_list:
                    for file_path in self.files_list:
                        file_success, file_error = self.send_file(number, file_path)
                        if not file_success:
                            files_success = False
                            last_error = file_error
                            break
                
                success = text_success and files_success
                
                if not success and attempt < max_attempts:
                    # Espera um pouco antes de tentar novamente
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
                interval += random.randint(1, 3)  # Adiciona entre 1 e 3 segundos aleatoriamente
                
            # Aguarda antes de enviar a próxima mensagem
            if idx < total_contacts:  # Não espera após o último contato
                self.status_var.set(f"Aguardando {interval}s antes da próxima mensagem...")
                for i in range(interval):
                    if not self.running:
                        break
                    time.sleep(1)
        
        # Após finalizar, mostra o frame de estatísticas
        if not self.stats_frame.winfo_ismapped():
            self.stats_frame.pack(fill=tk.X, padx=10, pady=5, after=self.stop_button)

        if self.running:  # Somente mostra mensagem se não foi interrompido
            self.status_var.set("Envio concluído")
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
    root = tk.Tk()
    app = WhatsAppMessengerGUI(root)
    root.mainloop()