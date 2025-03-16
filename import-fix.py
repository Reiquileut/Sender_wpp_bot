"""
Este script corrige erros de importação em arquivos Python,
especificamente o erro "cannot import name 'file dialog' from tkinter".

Execute este script no mesmo diretório onde está o executável.
"""

import os
import re
import sys

def get_base_dir():
    """Retorna o diretório base do aplicativo"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def fix_tkinter_imports(file_path):
    """Corrige as importações do tkinter no arquivo especificado"""
    print(f"Corrigindo importações em: {file_path}")
    
    # Lê o conteúdo do arquivo
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
        content = file.read()
    
    # Corrige importações incorretas
    fixed_content = content
    
    # Corrige 'file dialog' para 'filedialog'
    fixed_content = re.sub(
        r'from\s+tkinter\s+import\s+(?:[^,\n]*,\s*)*file dialog(?:\s*,\s*[^,\n]*)*', 
        lambda m: m.group(0).replace('file dialog', 'filedialog'),
        fixed_content
    )
    
    # Corrige outras variações possíveis do erro
    fixed_content = re.sub(
        r'from\s+tkinter\s+import\s+file dialog', 
        'from tkinter import filedialog',
        fixed_content
    )
    
    # Corrige possíveis erros de espaço
    fixed_content = re.sub(
        r'from\s+tkinter\s+import\s+filedialog ', 
        'from tkinter import filedialog',
        fixed_content
    )
    
    # Verifica se o conteúdo foi alterado
    if content != fixed_content:
        # Faz backup do arquivo original
        backup_path = file_path + '.bak'
        os.rename(file_path, backup_path)
        
        # Escreve o conteúdo corrigido
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(fixed_content)
        
        print(f"Arquivo corrigido: {file_path}")
        print(f"Backup criado em: {backup_path}")
        return True
    
    print(f"Nenhuma correção necessária para: {file_path}")
    return False

def find_and_fix_python_files():
    """Encontra e corrige todos os arquivos Python no diretório da aplicação"""
    base_dir = get_base_dir()
    print(f"Procurando arquivos Python em: {base_dir}")
    
    fixed_files = 0
    
    # Procura todos os arquivos Python
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if fix_tkinter_imports(file_path):
                    fixed_files += 1
    
    return fixed_files

def main():
    print("Iniciando correção de importações tkinter...")
    fixed_count = find_and_fix_python_files()
    
    if fixed_count > 0:
        print(f"\nCorreção concluída! {fixed_count} arquivo(s) foram corrigidos.")
        print("Por favor, reinicie o aplicativo.")
    else:
        print("\nNenhum arquivo precisou ser corrigido.")
        
    input("\nPressione Enter para sair...")

if __name__ == "__main__":
    main()
