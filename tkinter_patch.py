# tkinter_patch.py
import sys
import importlib

def patch_tkinter():
    # Registra uma função de importação personalizada para tkinter
    class TkinterFinder:
        def find_spec(self, fullname, path, target=None):
            if fullname.startswith('tkinter:'):
                # Converte tkinter:xxxx para tkinter.xxxx
                corrected = fullname.replace(':', '.')
                try:
                    # Carrega o módulo correto
                    module = importlib.import_module(corrected)
                    # Registra no sys.modules com o nome incorreto para facilitar a importação
                    sys.modules[fullname] = module
                    return importlib.util.find_spec(corrected)
                except ImportError:
                    pass
            return None

    # Adiciona o finder personalizado ao início da lista de finders
    sys.meta_path.insert(0, TkinterFinder())

# Aplica o patch imediatamente
patch_tkinter()