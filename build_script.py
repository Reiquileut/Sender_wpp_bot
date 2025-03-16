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

def run_command(cmd, cwd=None, env=None):
    """Executa um comando no shell."""
    print(f"Executando: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=True, cwd=cwd, env=env, 
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                           text=True)
    return result

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
    
    # Verifica se o Node.js está instalado no sistema
    try:
        result = run_command(["node", "--version"])
        print(f"Node.js encontrado no sistema: {result.stdout.strip()}")
        
        # Apenas anota a localização do Node.js no sistema, não precisamos baixar
        print("Usando Node.js do sistema para a compilação")
        return
    except:
        print("Node.js não encontrado no sistema. Tentando baixar...")
    
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
        
        # Verifica se o diretório extraído existe
        if not os.path.exists(node_extracted):
            print(f"Erro: Diretório extraído não encontrado: {node_extracted}")
            print("Conteúdo do diretório temp_node:")
            for root, dirs, files in os.walk(temp_dir):
                print(f"- Diretório: {root}")
                for d in dirs:
                    print(f"  - Subdir: {d}")
                for f in files:
                    print(f"  - Arquivo: {f}")
            
            # Tenta encontrar o diretório correto
            node_dirs = [d for d in os.listdir(temp_dir) if d.startswith("node-")]
            if node_dirs:
                node_extracted = os.path.join(temp_dir, node_dirs[0])
                print(f"Usando diretório alternativo: {node_extracted}")
            else:
                print("Nenhum diretório Node.js encontrado. Saindo.")
                sys.exit(1)
        
        # Verifica e cria o diretório de destino
        if not os.path.exists(node_dir):
            os.makedirs(node_dir)
            
        # Copia os arquivos
        print(f"Copiando arquivos de {node_extracted} para {node_dir}")
        for item in os.listdir(node_extracted):
            src = os.path.join(node_extracted, item)
            dst = os.path.join(node_dir, item)
            if os.path.isdir(src):
                if os.path.exists(dst):
                    shutil.rmtree(dst)
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
    
    # Verifica se os arquivos de origem existem
    server_js_path = os.path.join(server_src, "server.js")
    package_json_path = os.path.join(server_src, "package.json")
    
    if not os.path.exists(server_js_path):
        print(f"ERRO: Arquivo server.js não encontrado em {server_js_path}")
        # Procura em todo o diretório de origem
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                if file == "server.js":
                    server_js_path = os.path.join(root, file)
                    print(f"Encontrado arquivo server.js em {server_js_path}")
                    break
            if os.path.exists(server_js_path) and server_js_path != os.path.join(server_src, "server.js"):
                break
        
        if not os.path.exists(server_js_path):
            print("Arquivo server.js não encontrado. Saindo.")
            sys.exit(1)
    
    if not os.path.exists(package_json_path):
        print(f"ERRO: Arquivo package.json não encontrado em {package_json_path}")
        # Procura em todo o diretório de origem
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                if file == "package.json":
                    package_json_path = os.path.join(root, file)
                    print(f"Encontrado arquivo package.json em {package_json_path}")
                    break
            if os.path.exists(package_json_path) and package_json_path != os.path.join(server_src, "package.json"):
                break
        
        if not os.path.exists(package_json_path):
            print("Arquivo package.json não encontrado. Saindo.")
            sys.exit(1)
    
    # Copia os arquivos do servidor
    print(f"Copiando server.js de {server_js_path} para {server_dst}")
    shutil.copy2(server_js_path, server_dst)
    
    print(f"Copiando package.json de {package_json_path} para {server_dst}")
    shutil.copy2(package_json_path, server_dst)
    
    # Verifica se os arquivos foram copiados
    if not os.path.exists(os.path.join(server_dst, "server.js")):
        print(f"ERRO: Falha ao copiar server.js para {server_dst}")
    else:
        print(f"server.js copiado com sucesso para {server_dst}")
    
    if not os.path.exists(os.path.join(server_dst, "package.json")):
        print(f"ERRO: Falha ao copiar package.json para {server_dst}")
    else:
        print(f"package.json copiado com sucesso para {server_dst}")
    
    # Instala as dependências do servidor
    print("Instalando dependências do servidor...")
    
    # Verifica se o npm está disponível
    npm_cmd = "npm"
    try:
        run_command([npm_cmd, "--version"])
        print("npm está disponível para instalar dependências")
    except:
        print("ERRO: npm não está disponível no sistema")
        if platform.system() == "Windows":
            # Tenta encontrar npm.cmd no diretório bin/node se existir
            npm_cmd_path = os.path.join(build_dir, "bin", "node", "npm.cmd")
            if os.path.exists(npm_cmd_path):
                npm_cmd = npm_cmd_path
                print(f"Usando npm em: {npm_cmd}")
    
    # Executa npm install no diretório do servidor
    try:
        # Aumenta o tempo limite para npm install
        print(f"Executando {npm_cmd} install no diretório {server_dst}")
        result = run_command([npm_cmd, "install"], cwd=server_dst)
        print("Saída do npm install:")
        print(result.stdout)
        
        # Verifica se a pasta node_modules foi criada
        node_modules_path = os.path.join(server_dst, "node_modules")
        if os.path.exists(node_modules_path):
            print(f"node_modules instalado com sucesso em {node_modules_path}")
            # Lista alguns módulos importantes para verificação
            for module in ["express", "whatsapp-web.js", "cors", "body-parser", "multer", "qrcode-terminal"]:
                module_path = os.path.join(node_modules_path, module)
                if os.path.exists(module_path):
                    print(f"✓ Módulo {module} instalado")
                else:
                    print(f"✗ AVISO: Módulo {module} não encontrado")
        else:
            print(f"ERRO: node_modules não foi criado em {node_modules_path}")
    except Exception as e:
        print(f"ERRO ao instalar dependências: {e}")

def prepare_client_files(build_dir, source_dir):
    """Prepara os arquivos do cliente."""
    print("Preparando arquivos do cliente...")
    
    client_src = os.path.join(source_dir, "client")
    client_dst = os.path.join(build_dir, "client")
    
    # Cria o diretório de destino
    create_directory(client_dst)
    
    # Verifica se o arquivo de origem existe
    client_py_path = os.path.join(client_src, "whatsapp_messenger.py")
    
    if not os.path.exists(client_py_path):
        print(f"ERRO: Arquivo whatsapp_messenger.py não encontrado em {client_py_path}")
        # Se o arquivo não existir no diretório esperado, procura em todo o diretório de origem
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                if file == "whatsapp_messenger.py":
                    client_py_path = os.path.join(root, file)
                    print(f"Encontrado arquivo whatsapp_messenger.py em {client_py_path}")
                    break
            if os.path.exists(client_py_path) and client_py_path != os.path.join(client_src, "whatsapp_messenger.py"):
                break
                
        if not os.path.exists(client_py_path):
            print("Arquivo whatsapp_messenger.py não encontrado. Saindo.")
            sys.exit(1)
    
    # Copia o arquivo do cliente
    print(f"Copiando {client_py_path} para {client_dst}")
    shutil.copy2(client_py_path, client_dst)
    
    # Verifica se o arquivo foi copiado
    if not os.path.exists(os.path.join(client_dst, "whatsapp_messenger.py")):
        print(f"ERRO: Falha ao copiar whatsapp_messenger.py para {client_dst}")
    else:
        print(f"whatsapp_messenger.py copiado com sucesso para {client_dst}")

def build_executable(build_dir, dist_dir):
    """Compila o executável com PyInstaller."""
    print("Compilando o executável...")
    
    # Configura o spec do PyInstaller
    app_launcher = os.path.join(build_dir, "app_launcher.py")
    
    # Verifica se o arquivo app_launcher.py existe
    if not os.path.exists(app_launcher):
        print(f"ERRO: app_launcher.py não encontrado em {app_launcher}")
        # Procura em todo o diretório
        for root, dirs, files in os.walk(build_dir):
            for file in files:
                if file == "app_launcher.py":
                    app_launcher = os.path.join(root, file)
                    print(f"Encontrado arquivo app_launcher.py em {app_launcher}")
                    break
            if os.path.exists(app_launcher) and app_launcher != os.path.join(build_dir, "app_launcher.py"):
                break
                
        if not os.path.exists(app_launcher):
            print("Arquivo app_launcher.py não encontrado. Saindo.")
            sys.exit(1)
    
    # Pastas a serem incluídas no pacote
    additional_data = [
        (os.path.join(build_dir, "server"), "server"),
        (os.path.join(build_dir, "client"), "client"),
        (os.path.join(build_dir, "bin"), "bin")
    ]
    
    # Verifica se todas as pastas existem
    for src, _ in additional_data:
        if not os.path.exists(src):
            print(f"AVISO: Diretório não encontrado: {src}")
            create_directory(src)
    
    # Constrói a linha de comando para o PyInstaller
    pyinstaller_cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", PROJECT_NAME,
        "--onedir",  # Cria um diretório com o executável e dependências
        "--windowed",  # Não mostra a janela de console
        "--log-level", "DEBUG"  # Adiciona log detalhado para debug
    ]
    
    # Adiciona o ícone se existir
    icon_path = os.path.join(build_dir, "icon.ico")
    if os.path.exists(icon_path):
        pyinstaller_cmd.extend(["--icon", icon_path])
    
    # Adiciona os dados adicionais
    for src, dst in additional_data:
        if os.path.exists(src):
            # No Windows usa ponto e vírgula como separador
            sep = ";" if platform.system() == "Windows" else ":"
            data_arg = f"{src}{sep}{dst}"
            pyinstaller_cmd.extend(["--add-data", data_arg])
            print(f"Adicionando dados: {data_arg}")
            
            # Lista arquivos importantes para confirmação
            if dst == "server":
                server_js_path = os.path.join(src, "server.js")
                if os.path.exists(server_js_path):
                    print(f"✓ server.js será incluído no pacote")
                else:
                    print(f"✗ AVISO: server.js não encontrado em {server_js_path}")
                
                node_modules_path = os.path.join(src, "node_modules")
                if os.path.exists(node_modules_path):
                    print(f"✓ node_modules será incluído no pacote")
                    # Verifica o tamanho da pasta node_modules
                    node_modules_size = sum(os.path.getsize(os.path.join(dirpath, filename)) 
                                          for dirpath, dirnames, filenames in os.walk(node_modules_path) 
                                          for filename in filenames) / (1024*1024)  # em MB
                    print(f"  Tamanho de node_modules: {node_modules_size:.2f} MB")
                else:
                    print(f"✗ AVISO: node_modules não encontrado em {node_modules_path}")
        else:
            print(f"AVISO: Não foi possível incluir {src}, diretório não existe")
    
    # Adiciona o script principal no final
    pyinstaller_cmd.append(app_launcher)
    
    # Executa o PyInstaller
    try:
        print("Iniciando compilação com PyInstaller...")
        result = run_command(pyinstaller_cmd, cwd=build_dir)
        print("Saída do PyInstaller:")
        print(result.stdout)
    except Exception as e:
        print(f"ERRO ao executar PyInstaller: {e}")
        sys.exit(1)
    
    # Move o resultado para o diretório de distribuição
    pyinstaller_dist = os.path.join(build_dir, "dist", PROJECT_NAME)
    if os.path.exists(pyinstaller_dist):
        print(f"Movendo resultado para {dist_dir}")
        # Se o diretório de destino já existir, remove-o
        if os.path.exists(dist_dir):
            shutil.rmtree(dist_dir)
        # Move o diretório de distribuição para o destino final
        shutil.move(pyinstaller_dist, dist_dir)
    else:
        print(f"ERRO: Diretório de distribuição não encontrado: {pyinstaller_dist}")
        print("Verificando o que foi gerado:")
        for root, dirs, files in os.walk(os.path.join(build_dir, "dist")):
            print(f"- Diretório: {root}")
            for d in dirs:
                print(f"  - Subdir: {d}")
            for f in files:
                print(f"  - Arquivo: {f}")

def copy_required_files_manually(dist_dir, source_dir):
    """Copia manualmente os arquivos necessários que possam ter faltado."""
    print("Verificando e copiando arquivos necessários...")
    
    # 1. Verifica e cria o diretório server
    server_dist = os.path.join(dist_dir, "server")
    if not os.path.exists(server_dist):
        print(f"Criando diretório server em {server_dist}")
        os.makedirs(server_dist)
    
    # 2. Verifica e copia server.js
    server_js_src = os.path.join(source_dir, "server", "server.js")
    server_js_dst = os.path.join(server_dist, "server.js")
    if not os.path.exists(server_js_dst):
        if os.path.exists(server_js_src):
            print(f"Copiando server.js para {server_js_dst}")
            shutil.copy2(server_js_src, server_js_dst)
        else:
            # Procura em todo o diretório
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    if file == "server.js":
                        src = os.path.join(root, file)
                        print(f"Copiando server.js de {src} para {server_js_dst}")
                        shutil.copy2(src, server_js_dst)
                        break
                if os.path.exists(server_js_dst):
                    break
    
    # 3. Verifica e copia package.json
    package_json_src = os.path.join(source_dir, "server", "package.json")
    package_json_dst = os.path.join(server_dist, "package.json")
    if not os.path.exists(package_json_dst):
        if os.path.exists(package_json_src):
            print(f"Copiando package.json para {package_json_dst}")
            shutil.copy2(package_json_src, package_json_dst)
        else:
            # Procura em todo o diretório
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    if file == "package.json":
                        src = os.path.join(root, file)
                        print(f"Copiando package.json de {src} para {package_json_dst}")
                        shutil.copy2(src, package_json_dst)
                        break
                if os.path.exists(package_json_dst):
                    break
    
    # 4. Instala as dependências do Node.js no diretório server
    node_modules_dst = os.path.join(server_dist, "node_modules")
    if not os.path.exists(node_modules_dst):
        print(f"Tentando instalar dependências do Node.js em {server_dist}...")
        try:
            result = run_command(["npm", "install"], cwd=server_dist)
            print("Saída da instalação de dependências:")
            print(result.stdout)
            if os.path.exists(node_modules_dst):
                print("✓ Dependências do Node.js instaladas com sucesso")
            else:
                print("✗ Falha ao instalar dependências do Node.js")
        except Exception as e:
            print(f"ERRO ao instalar dependências: {e}")
            print("Você precisará instalar as dependências manualmente após a instalação")
            print("Execute 'npm install' na pasta server do executável")

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
        launcher_src = os.path.join(current_dir, "app_launcher.py")
        if not os.path.exists(launcher_src):
            print(f"ERRO: app_launcher.py não encontrado em {launcher_src}")
            # Procura em todo o diretório
            for root, dirs, files in os.walk(current_dir):
                for file in files:
                    if file == "app_launcher.py":
                        launcher_src = os.path.join(root, file)
                        print(f"Encontrado arquivo app_launcher.py em {launcher_src}")
                        break
                if os.path.exists(launcher_src) and launcher_src != os.path.join(current_dir, "app_launcher.py"):
                    break
            
            if not os.path.exists(launcher_src):
                print("Arquivo app_launcher.py não encontrado. Saindo.")
                sys.exit(1)
        
        print(f"Copiando app_launcher.py de {launcher_src} para {build_dir}")
        shutil.copy2(launcher_src, build_dir)
        
        # Prepara os ambientes
        prepare_python_environment(build_dir)
        prepare_node_environment(build_dir)
        
        # Prepara os arquivos do servidor e cliente
        prepare_server_files(build_dir, current_dir)
        prepare_client_files(build_dir, current_dir)
        
        # Constrói o executável
        build_executable(build_dir, dist_dir)
        
        # Copia manualmente arquivos que possam ter faltado
        copy_required_files_manually(dist_dir, current_dir)
        
        print(f"\nConstrução concluída com sucesso!")
        print(f"O executável está disponível em: {dist_dir}")
        print("\nIMPORTANTE: Se o executável não funcionar corretamente:")
        print("1. Execute o aplicativo")
        print("2. Clique no botão 'Verificar Arquivos'")
        print("3. Clique em 'Instalar Dependências'")
        print("4. Reinicie o aplicativo")
    
    except Exception as e:
        print(f"Erro durante a construção: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Pergunta se deseja limpar os arquivos temporários
        keep_temp = input("Deseja manter os arquivos temporários para depuração? (s/N): ")
        if keep_temp.lower() != 's':
            # Limpa os arquivos temporários
            if os.path.exists(build_dir):
                print("Limpando arquivos temporários...")
                shutil.rmtree(build_dir)

if __name__ == "__main__":
    main()