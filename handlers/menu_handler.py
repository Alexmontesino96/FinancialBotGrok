from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from config import DESCRIPTION, AMOUNT, CONFIRM, SELECT_TO_MEMBER, PAYMENT_AMOUNT, PAYMENT_CONFIRM
from ui.keyboards import Keyboards
from ui.messages import Messages
from ui.formatters import Formatters
from services.expense_service import ExpenseService
from services.payment_service import PaymentService
from services.family_service import FamilyService
from services.member_service import MemberService
from utils.context_manager import ContextManager
from utils.helpers import send_error

# Importaciones de otros manejadores
from handlers.expense_handler import crear_gasto, listar_gastos
from handlers.payment_handler import registrar_pago
from handlers.family_handler import show_balances, mostrar_info_familia, compartir_invitacion
from handlers.edit_handler import show_edit_options

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el menú principal para usuarios en una familia."""
    await update.message.reply_text(
        Messages.MAIN_MENU,
        reply_markup=Keyboards.get_main_menu_keyboard()
    )
    return ConversationHandler.END

async def handle_menu_option(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja las opciones del menú principal."""
    option = update.message.text
    
    # Imprimir para depuración
    print(f"Opción seleccionada: {option}")
    
    # Si ya tenemos el family_id en el contexto, no necesitamos verificar
    if "family_id" in context.user_data:
        family_id = context.user_data["family_id"]
        print(f"Ya tenemos el family_id en el contexto: {family_id}")
    else:
        # Verificar que el usuario esté en una familia
        telegram_id = str(update.effective_user.id)
        print(f"Solicitando información del miembro con telegram_id: {telegram_id}")
        
        # Obtener información del miembro directamente de la API
        status_code, member = MemberService.get_member(telegram_id)
        
        if status_code != 200 or not member or not member.get("family_id"):
            await update.message.reply_text(Messages.ERROR_NOT_IN_FAMILY)
            return ConversationHandler.END
        
        # Guardar el ID de la familia en el contexto
        family_id = member.get("family_id")
        context.user_data["family_id"] = family_id
        print(f"Family ID guardado en el contexto: {family_id}")
    
    # Manejar la opción seleccionada
    if option == "💰 Ver Balances":
        return await show_balances(update, context)
    elif option == "ℹ️ Info Familia":
        return await mostrar_info_familia(update, context)
    elif option == "💸 Crear Gasto":
        return await crear_gasto(update, context)
    elif option == "📋 Ver Gastos":
        return await listar_gastos(update, context)
    elif option == "💳 Registrar Pago":
        return await registrar_pago(update, context)
    elif option == "🔗 Compartir Invitación":
        return await compartir_invitacion(update, context)
    elif option == "✏️ Editar/Eliminar":
        return await show_edit_options(update, context)
    else:
        await update.message.reply_text(
            Messages.ERROR_INVALID_OPTION,
            reply_markup=Keyboards.get_main_menu_keyboard()
        )
        return ConversationHandler.END

async def handle_unknown_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja texto desconocido y muestra el menú principal."""
    await update.message.reply_text(
        "No entiendo ese comando. Aquí tienes el menú principal:",
        reply_markup=Keyboards.get_main_menu_keyboard()
    )
    return await show_main_menu(update, context) 