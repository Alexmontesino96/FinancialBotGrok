from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from ui.messages import Messages
from ui.formatters import Formatters
from services.family_service import FamilyService
from utils.context_manager import ContextManager
from utils.helpers import send_error, create_qr_code
import traceback

# Eliminamos la importación circular
# from handlers.menu_handler import show_main_menu

async def _show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Función auxiliar para mostrar el menú principal sin importación circular."""
    from handlers.menu_handler import show_main_menu
    return await show_main_menu(update, context)

async def show_balances(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra los balances de la familia."""
    try:
        # Obtener el ID de la familia del contexto
        family_id = ContextManager.get_family_id(context)
        print(f"Obteniendo balances para la familia con ID: {family_id}")
        
        if not family_id:
            print("No se encontró el ID de familia en el contexto")
            await update.message.reply_text(Messages.ERROR_NOT_IN_FAMILY)
            return ConversationHandler.END
        
        # Obtener el ID de Telegram del usuario
        telegram_id = str(update.effective_user.id)
        
        # Guardar el ID de Telegram en el contexto
        context.user_data["telegram_id"] = telegram_id
        
        # Obtener los balances usando el ID de Telegram como identificación
        print(f"Solicitando balances a la API para la familia {family_id} con telegram_id={telegram_id}")
        status_code, balances = FamilyService.get_family_balances(family_id, telegram_id)
        print(f"Respuesta de get_family_balances: status_code={status_code}, balances={balances}")
        
        if status_code >= 400 or not balances:
            error_msg = f"❌ Error al obtener los balances. Código de error: {status_code}"
            if isinstance(balances, dict) and "detail" in balances:
                error_msg += f"\nDetalle: {balances['detail']}"
            print(f"Error al obtener balances: {error_msg}")
            await update.message.reply_text(error_msg)
            # No mostrar el menú aquí, solo informar del error
            return ConversationHandler.END
        
        # Obtener los nombres de los miembros
        member_names = ContextManager.get_member_names(context)
        print(f"Nombres de miembros en el contexto: {member_names}")
        
        # Si no hay nombres en el contexto, intentar cargarlos
        if not member_names:
            print(f"No hay nombres de miembros en el contexto, intentando cargarlos")
            await ContextManager.load_family_members(context, family_id)
            member_names = ContextManager.get_member_names(context)
            print(f"Nombres de miembros cargados: {member_names}")
        
        # Formatear los balances
        print(f"Formateando balances: {balances}")
        formatted_balances = Formatters.format_balances(balances, member_names)
        
        # Enviar el mensaje con los balances
        await update.message.reply_text(
            f"📊 *Balances de la Familia*\n\n{formatted_balances}",
            parse_mode="Markdown"
        )
        
        return ConversationHandler.END
        
    except Exception as e:
        print(f"Error en show_balances: {str(e)}")
        traceback.print_exc()
        await send_error(update, context, str(e))
        return ConversationHandler.END

async def mostrar_info_familia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra información sobre la familia."""
    try:
        family_id = context.user_data.get("family_id")
        if not family_id:
            await update.message.reply_text(Messages.ERROR_NOT_IN_FAMILY)
            return ConversationHandler.END
            
        # Obtener el ID de Telegram del usuario
        telegram_id = str(update.effective_user.id)
        
        # Guardar el ID de Telegram en el contexto
        context.user_data["telegram_id"] = telegram_id
            
        # Obtener la información de la familia
        status_code, family = FamilyService.get_family(family_id, telegram_id)
        
        if status_code != 200 or not family:
            await update.message.reply_text(Messages.ERROR_GETTING_FAMILY_INFO)
            return ConversationHandler.END
        
        # Formatear la información
        family_name = family.get("name", "Sin nombre")
        members = family.get("members", [])
        
        # Formatear la lista de miembros de manera más eficiente
        members_text = "\n".join(
            f"- {member.get('name', 'Sin nombre')} {'👑' if member.get('is_admin') else ''}"
            for member in members
        )
        
        # Enviar el mensaje con la información
        message = (
            f"👪 *Información de la Familia*\n\n"
            f"*Nombre:* {family_name}\n"
            f"*ID:* `{family_id}`\n\n"
            f"*Miembros ({len(members)}):*\n{members_text}"
        )
        
        await update.message.reply_text(message, parse_mode="Markdown")
        return await _show_menu(update, context)
        
    except Exception as e:
        await send_error(update, context, str(e))
        return await _show_menu(update, context)

async def compartir_invitacion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Genera y comparte un código QR y un enlace para invitar a otros a la familia."""
    try:
        family_id = context.user_data.get("family_id")
        if not family_id:
            await update.message.reply_text(Messages.ERROR_NOT_IN_FAMILY)
            return ConversationHandler.END
            
        # Obtener el ID de Telegram del usuario
        telegram_id = str(update.effective_user.id)
        
        # Guardar el ID de Telegram en el contexto
        context.user_data["telegram_id"] = telegram_id
            
        # Obtener la información de la familia para verificar que existe
        status_code, family = FamilyService.get_family(family_id, telegram_id)
        
        if status_code != 200 or not family:
            await update.message.reply_text(Messages.ERROR_GETTING_FAMILY_INFO)
            return ConversationHandler.END
        
        # Obtener el nombre de la familia
        family_name = family.get("name", "Sin nombre")
        
        # Crear el enlace de invitación
        invite_link = f"https://t.me/{context.bot.username}?start=join_{family_id}"
        
        # Generar el código QR
        qr_image = create_qr_code(invite_link)
        
        # Enviar el mensaje con el código QR - Usando formato de texto simple para evitar problemas con Markdown
        await update.message.reply_photo(
            photo=qr_image,
            caption=f"🔗 Invitación a la Familia {family_name}\n\n"
                   f"Comparte este código QR o el siguiente enlace para invitar a alguien a unirse a tu familia:\n\n"
                   f"{invite_link}\n\n"
                   f"Instrucciones para el invitado:\n"
                   f"1. Haz clic en el enlace o escanea el código QR\n"
                   f"2. Se abrirá el bot @{context.bot.username}\n"
                   f"3. Presiona el botón 'INICIAR' o envía /start\n"
                   f"4. Serás añadido automáticamente a la familia {family_name}"
        )
        
        # Enviar también el ID de la familia por si el enlace no funciona - Usando formato de texto simple
        await update.message.reply_text(
            f"📝 ID de la familia: {family_id}\n\n"
            f"Si el enlace o el código QR no funcionan, puedes compartir este ID. "
            f"El invitado deberá seleccionar la opción '🔗 Unirse a Familia' e introducir este ID."
        )
        
        return await _show_menu(update, context)
        
    except Exception as e:
        print(f"Error en compartir_invitacion: {str(e)}")
        traceback.print_exc()
        await send_error(update, context, str(e))
        return await _show_menu(update, context) 