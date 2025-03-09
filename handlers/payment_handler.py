from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from config import SELECT_TO_MEMBER, PAYMENT_AMOUNT, CONFIRM
from ui.keyboards import Keyboards
from ui.messages import Messages
from services.payment_service import PaymentService
from services.family_service import FamilyService
from services.member_service import MemberService
from utils.context_manager import ContextManager
from utils.helpers import send_error

# Eliminamos la importación circular
# from handlers.menu_handler import show_main_menu

async def _show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Función auxiliar para mostrar el menú principal sin importación circular."""
    from handlers.menu_handler import show_main_menu
    return await show_main_menu(update, context)

async def registrar_pago(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia el flujo para registrar un pago."""
    try:
        # Limpiar datos previos
        if "payment_data" in context.user_data:
            del context.user_data["payment_data"]
        
        # Inicializar datos del pago
        context.user_data["payment_data"] = {}
        
        # Obtener el ID del usuario
        telegram_id = str(update.effective_user.id)
        print(f"Buscando miembro con telegram_id: {telegram_id}")
        
        # Verificar si el usuario está en una familia
        status_code, member = MemberService.get_member(telegram_id)
        print(f"Respuesta de get_member: status_code={status_code}, member={member}")
        
        if status_code != 200 or not member or not member.get("family_id"):
            await update.message.reply_text(
                Messages.ERROR_NOT_IN_FAMILY,
                reply_markup=Keyboards.remove_keyboard()
            )
            await _show_menu(update, context)
            return ConversationHandler.END
        
        # Obtener el ID de la familia
        family_id = member.get("family_id")
        print(f"ID de familia obtenido: {family_id}")
        
        # Obtener el ID del miembro
        from_member = member.get("id", telegram_id)
        print(f"ID del miembro obtenido: {from_member}")
        
        # Guardar el ID del pagador
        context.user_data["payment_data"]["from_member"] = from_member
        
        # Obtener los balances de la familia
        status_code, balances = FamilyService.get_family_balances(family_id)
        print(f"Respuesta de get_family_balances: status_code={status_code}, balances={balances}")
        
        if status_code != 200 or not balances:
            await update.message.reply_text(
                f"❌ Error al obtener los balances. Código de error: {status_code}",
                reply_markup=Keyboards.remove_keyboard()
            )
            await _show_menu(update, context)
            return ConversationHandler.END
        
        # Obtener los miembros de la familia para mostrar nombres
        status_code, family = FamilyService.get_family(family_id)
        print(f"Respuesta de get_family: status_code={status_code}, family={family}")
        
        # Preparar la lista de acreedores (a quienes debe dinero)
        debtors = []
        
        # Buscar el balance del miembro actual
        for balance in balances:
            if balance.get("member_id") == str(from_member):
                # Añadir todas las deudas del miembro
                for debt in balance.get("debts", []):
                    creditor_name = debt.get("to", "")
                    amount = debt.get("amount", 0)
                    
                    # Buscar el ID del acreedor en los miembros de la familia
                    creditor_id = None
                    for member in family.get("members", []):
                        if member.get("name") == creditor_name:
                            creditor_id = member.get("id")
                            break
                    
                    if creditor_id and amount > 0:
                        debtors.append({
                            "id": creditor_id,
                            "name": creditor_name,
                            "amount": amount
                        })
                break
        
        print(f"Acreedores encontrados (a quienes debe dinero): {debtors}")
        
        if not debtors:
            await update.message.reply_text(
                Messages.CREATE_PAYMENT_NO_DEBTS,
                reply_markup=Keyboards.remove_keyboard()
            )
            await _show_menu(update, context)
            return ConversationHandler.END
        
        # Guardar los deudores en el contexto
        context.user_data["payment_data"]["debtors"] = debtors
        
        # Crear teclado con los acreedores (a quienes debe dinero)
        keyboard = []
        for debtor in debtors:
            keyboard.append([f"{debtor['name']} (${debtor['amount']:.2f})"])
        
        # Agregar botón de cancelar
        keyboard.append(["❌ Cancelar"])
        
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        
        await update.message.reply_text(
            Messages.CREATE_PAYMENT_INTRO,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        return SELECT_TO_MEMBER
        
    except Exception as e:
        print(f"Error al registrar pago: {str(e)}")
        await send_error(update, context, str(e))
        await _show_menu(update, context)
        return ConversationHandler.END

async def select_to_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe el miembro al que se le pagará."""
    option = update.message.text
    
    if option == "❌ Cancelar":
        await update.message.reply_text(
            Messages.CANCEL_PAYMENT,
            reply_markup=Keyboards.remove_keyboard()
        )
        await _show_menu(update, context)
        return ConversationHandler.END
    
    # Buscar el miembro seleccionado
    debtors = context.user_data["payment_data"].get("debtors", [])
    selected_debtor = None
    
    for debtor in debtors:
        if option.startswith(debtor["name"]):
            selected_debtor = debtor
            break
    
    if not selected_debtor:
        await update.message.reply_text(
            "❌ Miembro no válido. Por favor, selecciona un miembro de la lista:"
        )
        return SELECT_TO_MEMBER
    
    # Guardar el miembro seleccionado
    context.user_data["payment_data"]["to_member"] = selected_debtor["id"]
    context.user_data["payment_data"]["to_member_name"] = selected_debtor["name"]
    context.user_data["payment_data"]["max_amount"] = selected_debtor["amount"]
    
    await update.message.reply_text(
        Messages.CREATE_PAYMENT_AMOUNT,
        parse_mode="Markdown",
        reply_markup=Keyboards.get_cancel_keyboard()
    )
    return PAYMENT_AMOUNT

async def get_payment_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe el monto del pago y muestra la confirmación."""
    try:
        # Intentar convertir a float
        amount_text = update.message.text.replace(',', '.')
        amount = float(amount_text)
        
        if amount <= 0:
            await update.message.reply_text(Messages.ERROR_INVALID_AMOUNT)
            return PAYMENT_AMOUNT
        
        max_amount = context.user_data["payment_data"].get("max_amount", 0)
        
        if amount > max_amount:
            await update.message.reply_text(
                f"❌ El monto máximo que puedes pagar es ${max_amount:.2f}. Por favor, ingresa un monto menor o igual:"
            )
            return PAYMENT_AMOUNT
        
        # Guardar el monto
        context.user_data["payment_data"]["amount"] = amount
        
        # Mostrar confirmación
        return await show_payment_confirmation(update, context)
        
    except ValueError:
        await update.message.reply_text(Messages.ERROR_INVALID_AMOUNT)
        return PAYMENT_AMOUNT

async def show_payment_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra la confirmación del pago."""
    payment_data = context.user_data["payment_data"]
    
    # Obtener los nombres
    member_names = ContextManager.get_member_names(context)
    from_member_name = member_names.get(payment_data["from_member"], "Tú")
    to_member_name = payment_data["to_member_name"]
    
    # Formatear detalles
    details = (
        f"*De:* {from_member_name}\n"
        f"*Para:* {to_member_name}\n"
        f"*Monto:* ${payment_data['amount']:.2f}"
    )
    
    await update.message.reply_text(
        Messages.CONFIRM_PAYMENT.format(details=details),
        parse_mode="Markdown",
        reply_markup=Keyboards.get_confirmation_keyboard()
    )
    return CONFIRM

async def confirm_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirma y crea el pago."""
    option = update.message.text
    
    if option == "❌ Cancelar":
        await update.message.reply_text(
            Messages.CANCEL_PAYMENT,
            reply_markup=Keyboards.remove_keyboard()
        )
        await _show_menu(update, context)
        return ConversationHandler.END
    
    if option != "✅ Confirmar":
        await update.message.reply_text("❌ Por favor, confirma o cancela el pago:")
        return CONFIRM
    
    # Preparar datos para la API
    payment_data = context.user_data["payment_data"]
    
    try:
        # Enviar a la API
        status_code, response = PaymentService.create_payment(
            from_member=payment_data["from_member"],
            to_member=payment_data["to_member"],
            amount=payment_data["amount"]
        )
        
        if status_code >= 400:
            await update.message.reply_text(
                f"❌ Error al registrar el pago. Código de error: {status_code}",
                reply_markup=Keyboards.remove_keyboard()
            )
        else:
            await update.message.reply_text(
                Messages.SUCCESS_PAYMENT_CREATED,
                reply_markup=Keyboards.remove_keyboard()
            )
        
        # Limpiar datos del pago
        if "payment_data" in context.user_data:
            del context.user_data["payment_data"]
        
        # Volver al menú principal
        await _show_menu(update, context)
        return ConversationHandler.END
        
    except Exception as e:
        await send_error(update, context, str(e))
        # Limpiar datos del pago
        if "payment_data" in context.user_data:
            del context.user_data["payment_data"]
        await _show_menu(update, context)
        return ConversationHandler.END 