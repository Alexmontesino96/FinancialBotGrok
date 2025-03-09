from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from config import DESCRIPTION, AMOUNT, CONFIRM
from ui.keyboards import Keyboards
from ui.messages import Messages
from ui.formatters import Formatters
from services.expense_service import ExpenseService
from utils.context_manager import ContextManager
from utils.helpers import send_error
from services.member_service import MemberService
import traceback

# Eliminamos la importación circular
# from handlers.menu_handler import show_main_menu

async def _show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Función auxiliar para mostrar el menú principal sin importación circular."""
    from handlers.menu_handler import show_main_menu
    return await show_main_menu(update, context)

async def crear_gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia el flujo para crear un gasto."""
    try:
        # Verificar que el usuario está en una familia
        telegram_id = str(update.effective_user.id)
        status_code, member = MemberService.get_member(telegram_id)
        
        if status_code != 200 or not member or not member.get("family_id"):
            await update.message.reply_text(
                Messages.ERROR_NOT_IN_FAMILY,
                reply_markup=Keyboards.remove_keyboard()
            )
            return ConversationHandler.END
        
        # Limpiar datos previos e inicializar con la información del miembro
        context.user_data["expense_data"] = {
            "telegram_id": telegram_id,
            "member_id": member.get("id"),
            "family_id": member.get("family_id")
        }
        
        await update.message.reply_text(
            Messages.CREATE_EXPENSE_INTRO,
            parse_mode="Markdown",
            reply_markup=Keyboards.get_cancel_keyboard()
        )
        return DESCRIPTION
        
    except Exception as e:
        print(f"Error en crear_gasto: {str(e)}")
        traceback.print_exc()
        await send_error(update, context, str(e))
        return ConversationHandler.END

async def get_expense_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe la descripción del gasto y pide el monto."""
    try:
        description = update.message.text
        
        if description == "❌ Cancelar":
            await update.message.reply_text(
                Messages.CANCEL_OPERATION,
                reply_markup=Keyboards.get_main_menu_keyboard()
            )
            return ConversationHandler.END
        
        # Guardar la descripción
        context.user_data["expense_data"]["description"] = description
        
        await update.message.reply_text(
            Messages.CREATE_EXPENSE_AMOUNT.format(description=description),
            parse_mode="Markdown",
            reply_markup=Keyboards.get_cancel_keyboard()
        )
        return AMOUNT
    except Exception as e:
        print(f"Error en get_expense_description: {str(e)}")
        traceback.print_exc()
        await send_error(update, context, str(e))
        return ConversationHandler.END

async def get_expense_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe el monto del gasto y muestra la confirmación."""
    try:
        amount_text = update.message.text
        
        if amount_text == "❌ Cancelar":
            await update.message.reply_text(
                Messages.CANCEL_OPERATION,
                reply_markup=Keyboards.get_main_menu_keyboard()
            )
            return ConversationHandler.END
        
        # Validar y convertir el monto
        amount_text = amount_text.replace(',', '.').strip().replace('$', '')
        try:
            amount = float(amount_text)
        except ValueError:
            await update.message.reply_text(
                Messages.ERROR_INVALID_AMOUNT,
                reply_markup=Keyboards.get_cancel_keyboard()
            )
            return AMOUNT
        
        if amount <= 0:
            await update.message.reply_text(
                Messages.ERROR_INVALID_AMOUNT,
                reply_markup=Keyboards.get_cancel_keyboard()
            )
            return AMOUNT
        
        # Guardar el monto
        expense_data = context.user_data["expense_data"]
        expense_data["amount"] = amount
        
        # Ya tenemos el member_id del paso anterior
        if not expense_data.get("member_id"):
            await update.message.reply_text(
                Messages.ERROR_MEMBER_NOT_FOUND,
                reply_markup=Keyboards.remove_keyboard()
            )
            await _show_menu(update, context)
            return ConversationHandler.END
        
        # Mostrar resumen del gasto
        await update.message.reply_text(
            Messages.CREATE_EXPENSE_CONFIRM.format(
                description=expense_data['description'],
                amount=expense_data['amount'],
                paid_by="Tú"
            ),
            parse_mode="Markdown",
            reply_markup=Keyboards.get_confirmation_keyboard()
        )
        return CONFIRM
        
    except Exception as e:
        print(f"Error en get_expense_amount: {str(e)}")
        traceback.print_exc()
        await send_error(update, context, str(e))
        return ConversationHandler.END

async def show_expense_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra la confirmación del gasto."""
    expense_data = context.user_data["expense_data"]
    
    # Obtener el nombre del pagador
    member_names = ContextManager.get_member_names(context)
    paid_by_name = member_names.get(expense_data["paid_by"], "Tú")
    
    # Formatear detalles
    details = (
        f"*Descripción:* {expense_data['description']}\n"
        f"*Monto:* ${expense_data['amount']:.2f}\n"
        f"*Pagado por:* {paid_by_name}\n"
        f"*Dividido entre:* Todos los miembros por igual"
    )
    
    await update.message.reply_text(
        Messages.CONFIRM_EXPENSE.format(details=details),
        parse_mode="Markdown",
        reply_markup=Keyboards.get_confirmation_keyboard()
    )
    return CONFIRM

async def confirm_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirma y crea el gasto."""
    try:
        option = update.message.text
        
        if option == "❌ Cancelar":
            await update.message.reply_text(
                Messages.CANCEL_OPERATION,
                reply_markup=Keyboards.get_main_menu_keyboard()
            )
            return ConversationHandler.END
            
        elif option == "✅ Confirmar":
            expense_data = context.user_data["expense_data"]
            
            # Obtener el telegram_id del usuario
            telegram_id = expense_data.get("telegram_id") or str(update.effective_user.id)
            
            # Crear el gasto usando el member_id guardado y el telegram_id
            status_code, response = ExpenseService.create_expense(
                description=expense_data["description"],
                amount=expense_data["amount"],
                paid_by=expense_data["member_id"],
                telegram_id=telegram_id
            )
            
            print(f"Respuesta de create_expense: status_code={status_code}, response={response}")
            
            if status_code not in [200, 201]:
                await update.message.reply_text(
                    Messages.ERROR_CREATING_EXPENSE,
                    reply_markup=Keyboards.get_main_menu_keyboard()
                )
                return ConversationHandler.END
            
            # Mostrar mensaje de éxito
            message = (
                f"✅ *Gasto Creado Exitosamente*\n\n"
                f"*Descripción:* {expense_data['description']}\n"
                f"*Monto:* ${expense_data['amount']:.2f}\n"
                f"*Pagado por:* Tú\n"
                f"*ID del Gasto:* `{response.get('id', 'N/A')}`"
            )
            
            await update.message.reply_text(
                message,
                parse_mode="Markdown",
                reply_markup=Keyboards.get_main_menu_keyboard()
            )
            
            # Limpiar datos del gasto
            if "expense_data" in context.user_data:
                del context.user_data["expense_data"]
            
            return ConversationHandler.END
        
        else:
            await update.message.reply_text(
                Messages.ERROR_INVALID_OPTION,
                reply_markup=Keyboards.get_confirmation_keyboard()
            )
            return CONFIRM
            
    except Exception as e:
        print(f"Error en confirm_expense: {str(e)}")
        traceback.print_exc()
        await send_error(update, context, str(e))
        if "expense_data" in context.user_data:
            del context.user_data["expense_data"]
        await update.message.reply_text(
            "Volviendo al menú principal...",
            reply_markup=Keyboards.get_main_menu_keyboard()
        )
        return ConversationHandler.END

async def listar_gastos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra la lista de gastos de la familia."""
    try:
        # Verificar si tenemos el family_id en el contexto
        family_id = context.user_data.get("family_id")
        telegram_id = str(update.effective_user.id)
        
        # Si no tenemos el family_id, intentar obtenerlo
        if not family_id:
            print("No se encontró family_id en el contexto, intentando obtenerlo")
            status_code, member = MemberService.get_member(telegram_id)
            
            if status_code != 200 or not member or not member.get("family_id"):
                await update.message.reply_text(
                    Messages.ERROR_NOT_IN_FAMILY,
                    reply_markup=Keyboards.get_main_menu_keyboard()
                )
                return ConversationHandler.END
            
            # Guardar el ID de la familia en el contexto
            family_id = member.get("family_id")
            context.user_data["family_id"] = family_id
            print(f"Family ID obtenido y guardado en el contexto: {family_id}")
        else:
            print(f"Usando family_id del contexto: {family_id}")
        
        # Obtener los gastos - Asegurarse de que family_id sea un valor válido
        if not family_id:
            print("Error: family_id es None o vacío")
            await update.message.reply_text(
                "❌ Error al obtener los gastos: No se pudo determinar la familia",
                reply_markup=Keyboards.get_main_menu_keyboard()
            )
            return ConversationHandler.END
        
        print(f"Solicitando gastos para la familia con ID: {family_id}, telegram_id: {telegram_id}")
        status_code, expenses = ExpenseService.get_family_expenses(family_id, telegram_id)
        
        print(f"Respuesta de get_family_expenses: status_code={status_code}, expenses={expenses}")
        
        if status_code >= 400:
            print(f"Error al obtener gastos: status_code={status_code}, expenses={expenses}")
            await update.message.reply_text(
                f"❌ Error al obtener los gastos. Código de error: {status_code}",
                reply_markup=Keyboards.get_main_menu_keyboard()
            )
            return ConversationHandler.END
        
        # Obtener los nombres de los miembros
        member_names = context.user_data.get("member_names", {})
        print(f"Nombres de miembros en el contexto: {member_names}")
        
        # Si no hay nombres en el contexto, intentar cargarlos
        if not member_names:
            print("No se encontraron nombres de miembros en el contexto, intentando cargarlos")
            await ContextManager.load_family_members(context, family_id)
            member_names = context.user_data.get("member_names", {})
            print(f"Nombres de miembros cargados: {member_names}")
        
        # Formatear los gastos
        print(f"Formateando gastos: {expenses}")
        formatted_expenses = Formatters.format_expenses(expenses, member_names)
        print(f"Gastos formateados: {formatted_expenses}")
        
        if not formatted_expenses:
            await update.message.reply_text(
                "📋 No hay gastos registrados en esta familia.",
                reply_markup=Keyboards.get_main_menu_keyboard()
            )
        else:
            await update.message.reply_text(
                f"📋 *Gastos de la Familia*\n\n{formatted_expenses}",
                parse_mode="Markdown",
                reply_markup=Keyboards.get_main_menu_keyboard()
            )
        
        # No llamamos a _show_menu aquí para evitar duplicar el menú
        return ConversationHandler.END
        
    except Exception as e:
        print(f"Error en listar_gastos: {str(e)}")
        traceback.print_exc()
        await send_error(update, context, str(e))
        await update.message.reply_text(
            "Volviendo al menú principal...",
            reply_markup=Keyboards.get_main_menu_keyboard()
        )
        return ConversationHandler.END 