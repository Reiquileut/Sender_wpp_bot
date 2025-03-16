# hook-custom.py
from PyInstaller.utils.hooks import collect_submodules

# Coleta todos os submódulos do tkinter
hiddenimports = collect_submodules('tkinter')

# Adiciona manualmente os módulos problemáticos
hiddenimports.extend([
    'tkinter.filedialog',
    'tkinter.messagebox',
    'tkinter.scrolledtext'
])