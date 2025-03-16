import os
import sys
import shutil
import subprocess
import platform
import zipfile
import requests
import tempfile
from pathlib import Path

# Constantes
PROJECT_NAME = "WhatsApp Messenger Pro"
VERSION = "1.0.0"

def create_directory(path):
    """Cria um diretório se ele não existir."""
    if not os.path.exists(path):
        os.makedirs(path)
    return path

def download_file(url, destination):
    """Baixa um arquivo da Internet."""
    print(f"Baixando {url}...")
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(destination, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    print(f"Download concluído: {destination}")

def extract_zip(zip_path, extract_to):
    """Extrai um arquivo ZIP."""
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

def run_command(cmd, cwd=None):
    """Executa um comando no shell."""
    print(f"Executando: {' '.join(cmd)}")
    subprocess.run(cmd, check=True, cwd=cwd)

def prepare_python_environment(build_dir):
    """Prepara o ambiente Python."""
    print("Preparando ambiente Python...")
    
    # Verifica se o pip está instalado
    try:
        run_command([sys.executable, "-m", "pip", "--version"])
    except:
        print("Erro: pip não está instalado. Por favor, instale o pip antes de continuar.")
        sys.exit(1)
    
    # Instala as dependências de empacotamento
    print("Instalando dependências para empacotamento...")
    run_command([sys.executable, "-m", "pip", "install", "pyinstaller", "requests"])
    
    # Instala as dependências do projeto
    print("Instalando dependências do projeto...")
    run_command([
        sys.executable, "-m", "pip", "install",
        "pandas", "requests", "pillow", "ttkbootstrap"
    ])

def prepare_node_environment(build_dir):
    """Prepara o ambiente Node.js."""
    print("Preparando ambiente Node.js...")
    
    node_dir = os.path.join(build_dir, "bin", "node")
    create_directory(node_dir)
    
    # Baixa Node.js de acordo com o sistema operacional
    if platform.system() == "Windows":
        node_zip = os.path.join(build_dir, "node.zip")
        node_url = "https://nodejs.org/dist/v18.15.0/node-v18.15.0-win-x64.zip"
        download_file(node_url, node_zip)
        
        # Extrai o Node.js
        temp_dir = os.path.join(build_dir, "temp_node")
        create_directory(temp_dir)
        extract_zip(node_zip, temp_dir)
        
        # Move os arquivos do Node.js para o diretório correto
        node_extracted = os.path.join(temp_dir, "node-v18.15.0-win-x64")
        for item in os.listdir(node_extracted):
            src = os.path.join(node_extracted, item)
            dst = os.path.join(node_dir, item)
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
        
        # Limpa arquivos temporários
        shutil.rmtree(temp_dir)
        os.remove(node_zip)
    
    else:
        # Em sistemas Linux/Mac, vamos confiar no Node.js instalado no sistema
        print("Para sistemas não-Windows, o Node.js deve estar instalado no sistema.")
        try:
            run_command(["node", "--version"])
        except:
            print("Erro: Node.js não está instalado ou não está no PATH.")
            print("Por favor, instale o Node.js antes de continuar.")
            sys.exit(1)

def prepare_server_files(build_dir, source_dir):
    """Prepara os arquivos do servidor."""
    print("Preparando arquivos do servidor...")
    
    server_src = os.path.join(source_dir, "server")
    server_dst = os.path.join(build_dir, "server")
    
    # Cria o diretório de destino
    create_directory(server_dst)
    
    # Copia os arquivos do servidor
    shutil.copy2(os.path.join(server_src, "server.js"), server_dst)
    shutil.copy2(os.path.join(server_src, "package.json"), server_dst)
    
    # Instala as dependências do servidor
    print("Instalando dependências do servidor...")
    if platform.system() == "Windows":
        npm_path = os.path.join(build_dir, "bin", "node", "npm.cmd")
        run_command([npm_path, "install"], cwd=server_dst)
    else:
        run_command(["npm", "install"], cwd=server_dst)

def prepare_client_files(build_dir, source_dir):
    """Prepara os arquivos do cliente."""
    print("Preparando arquivos do cliente...")
    
    client_src = os.path.join(source_dir, "client")
    client_dst = os.path.join(build_dir, "client")
    
    # Cria o diretório de destino
    create_directory(client_dst)
    
    # Copia os arquivos do cliente
    shutil.copy2(os.path.join(client_src, "whatsapp_messenger.py"), client_dst)

def build_executable(build_dir, dist_dir):
    """Compila o executável com PyInstaller."""
    print("Compilando o executável...")
    
    # Configura o spec do PyInstaller
    app_launcher = os.path.join(build_dir, "app_launcher.py")
    
    # Pastas a serem incluídas no pacote
    additional_data = [
        ("server", "server"),
        ("client", "client"),
        ("bin", "bin")
    ]
    
    # Constrói a linha de comando para o PyInstaller
    pyinstaller_cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", PROJECT_NAME,
        "--onedir",  # Cria um diretório com o executável e dependências
        "--windowed",  # Não mostra a janela de console
        "--icon", os.path.join(build_dir, "icon.ico") if os.path.exists(os.path.join(build_dir, "icon.ico")) else None,
        app_launcher
    ]
    
    # Adiciona os dados adicionais
    for src, dst in additional_data:
        src_path = os.path.join(build_dir, src)
        if os.path.exists(src_path):
            pyinstaller_cmd.extend(["--add-data", f"{src_path}{os.pathsep}{dst}"])
    
    # Remove opções None (caso não exista ícone)
    pyinstaller_cmd = [x for x in pyinstaller_cmd if x is not None]
    
    # Executa o PyInstaller
    run_command(pyinstaller_cmd, cwd=build_dir)
    
    # Move o resultado para o diretório de distribuição
    pyinstaller_dist = os.path.join(build_dir, "dist", PROJECT_NAME)
    if os.path.exists(pyinstaller_dist):
        # Se o diretório de destino já existir, remove-o
        if os.path.exists(dist_dir):
            shutil.rmtree(dist_dir)
        # Move o diretório de distribuição para o destino final
        shutil.move(pyinstaller_dist, dist_dir)

def main():
    # Diretório atual
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Diretório de construção
    build_dir = os.path.join(current_dir, "build_tmp")
    create_directory(build_dir)
    
    # Diretório de distribuição
    dist_dir = os.path.join(current_dir, "dist", PROJECT_NAME)
    create_directory(os.path.dirname(dist_dir))
    
    try:
        # Copia o launcher para o diretório de construção
        shutil.copy2(os.path.join(current_dir, "app_launcher.py"), build_dir)
        
        # Prepara os ambientes
        prepare_python_environment(build_dir)
        prepare_node_environment(build_dir)
        
        # Prepara os arquivos do servidor e cliente
        prepare_server_files(build_dir, current_dir)
        prepare_client_files(build_dir, current_dir)
        
        # Constrói o executável
        build_executable(build_dir, dist_dir)
        
        print(f"\nConstrução concluída com sucesso!")
        print(f"O executável está disponível em: {dist_dir}")
    
    except Exception as e:
        print(f"Erro durante a construção: {e}")
    
    finally:
        # Limpa os arquivos temporários
        if os.path.exists(build_dir):
            print("Limpando arquivos temporários...")
            shutil.rmtree(build_dir)

if __name__ == "__main__":
    main()
