import qrcode
from io import BytesIO
from telegram import Update
from telegram.ext import ContextTypes

async def send_error(update: Update, context: ContextTypes.DEFAULT_TYPE, message: str):
    """Envía un mensaje de error al usuario.
    
    Args:
        update: Objeto Update de Telegram
        context: Contexto de Telegram
        message: Mensaje de error
    """
    await update.message.reply_text(f"❌ Error: {message}")

def create_qr_code(data):
    """Crea un código QR con los datos proporcionados.
    
    Args:
        data: Datos para el código QR
        
    Returns:
        BytesIO: Objeto con la imagen del código QR
    """
    # Crear un objeto QR
    qr = qrcode.QRCode(
        version=1,               # Controla el tamaño del QR (1 es el más pequeño)
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,             # El tamaño de cada "cuadradito" del QR
        border=4,                # El grosor del borde en cuadros
    )

    # Agregar los datos al objeto QR
    qr.add_data(data)
    qr.make(fit=True)

    # Crear la imagen
    img = qr.make_image(fill_color="black", back_color="white")

    bio = BytesIO()
    bio.name = 'codigo_qr.png'  # Nombre "ficticio" para el archivo
    img.save(bio, 'PNG')
    bio.seek(0)

    return bio

def parse_deep_link(args):
    """Parsea los argumentos de un enlace profundo.
    
    Args:
        args: Lista de argumentos del enlace profundo
        
    Returns:
        tuple: (tipo, valor) o (None, None) si no es un enlace profundo válido
    """
    if not args:
        return None, None
    
    arg = args[0]
    if arg.startswith("join_"):
        return "join", arg.replace("join_", "")
    
    return None, None 