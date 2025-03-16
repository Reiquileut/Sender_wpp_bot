# qrcode_handler.py
import io
import qrcode
from PIL import Image, ImageTk
import tkinter as tk

def generate_qr_image(data, box_size=10, border=4):
    """
    Gera uma imagem de QR code a partir de uma string de dados.
    
    Args:
        data (str): Texto/dados para codificar no QR code
        box_size (int): Tamanho de cada "caixa" do QR code
        border (int): Borda ao redor do QR code
        
    Returns:
        PIL.Image: Imagem do QR code gerada
    """
    # Cria o QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    # Cria uma imagem a partir do QR code
    img = qr.make_image(fill_color="black", back_color="white")
    return img

def update_qr_display(text_data, image_label, size=(250, 250)):
    """
    Atualiza um widget de label com a imagem do QR code gerada a partir do texto.
    
    Args:
        text_data (str): Texto do QR code
        image_label (tk.Label): Widget Label onde a imagem será exibida
        size (tuple): Tamanho para redimensionar a imagem (width, height)
    """
    if not text_data:
        # Se não houver dados, limpa a imagem no label
        image_label.config(image='')
        image_label.image = None
        return
    
    try:
        # Gera a imagem do QR code a partir do texto
        qr_img = generate_qr_image(text_data)
        
        # Redimensiona a imagem conforme necessário
        qr_img = qr_img.resize(size, Image.LANCZOS)
        
        # Converte para formato compatível com tkinter
        tk_img = ImageTk.PhotoImage(qr_img)
        
        # Atualiza o widget com a nova imagem
        image_label.config(image=tk_img)
        image_label.image = tk_img  # Mantém referência para evitar coleta de lixo
    except Exception as e:
        print(f"Erro ao gerar imagem do QR code: {e}")
        image_label.config(image='')
        image_label.image = None