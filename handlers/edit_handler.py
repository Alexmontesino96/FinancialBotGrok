from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from ui.keyboards import Keyboards
from ui.messages import Messages
from ui.formatters import Formatters
from services.expense_service import ExpenseService
from services.payment_service import PaymentService
from services.member_service import MemberService
from utils.context_manager import ContextManager
from utils.helpers import send_error
from config import EDIT_OPTION, SELECT_EXPENSE, SELECT_PAYMENT, CONFIRM_DELETE, EDIT_EXPENSE_AMOUNT
import traceback

# Estados para la conversación
# Ahora importados desde config.py

async def show_edit_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra las opciones para editar o eliminar gastos y pagos."""
    try:
        # Verificar que el usuario está en una familia
        family_id = context.user_data.get("family_id")
        telegram_id = str(update.effective_user.id)
        
        # Si no hay family_id en el contexto, intentar obtenerlo
        if not family_id:
            print(f"No hay family_id en el contexto, intentando obtenerlo para el usuario {telegram_id}")
            is_in_family = await ContextManager.check_user_in_family(context, telegram_id)
            
            if not is_in_family:
                await update.message.reply_text(
                    Messages.ERROR_NOT_IN_FAMILY,
                    reply_markup=Keyboards.get_main_menu_keyboard()
                )
                return ConversationHandler.END
            
            family_id = context.user_data.get("family_id")
            print(f"Family ID obtenido y guardado en el contexto: {family_id}")
        
        # Limpiar datos previos
        if "edit_data" in context.user_data:
            del context.user_data["edit_data"]
        
        # Inicializar datos de edición
        context.user_data["edit_data"] = {}
        
        # Mostrar opciones
        await update.message.reply_text(
            Messages.EDIT_OPTIONS,
            reply_markup=Keyboards.get_edit_options_keyboard()
        )
        return EDIT_OPTION
    
    except Exception as e:
        print(f"Error en show_edit_options: {str(e)}")
        traceback.print_exc()
        await send_error(update, context, str(e))
        return ConversationHandler.END

async def handle_edit_option(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja la selección de la opción de edición o eliminación."""
    try:
        option = update.message.text
        
        # Guardar la opción seleccionada
        context.user_data["edit_data"]["option"] = option
        
        # Obtener el ID de la familia y el ID de Telegram
        family_id = context.user_data.get("family_id")
        telegram_id = str(update.effective_user.id)
        
        # Si no hay family_id en el contexto, intentar obtenerlo
        if not family_id:
            print(f"No hay family_id en el contexto, intentando obtenerlo para el usuario {telegram_id}")
            is_in_family = await ContextManager.check_user_in_family(context, telegram_id)
            
            if not is_in_family:
                await update.message.reply_text(
                    Messages.ERROR_NOT_IN_FAMILY,
                    reply_markup=Keyboards.get_main_menu_keyboard()
                )
                return ConversationHandler.END
            
            family_id = context.user_data.get("family_id")
            print(f"Family ID obtenido y guardado en el contexto: {family_id}")
        
        if option == "📝 Editar Gastos":
            # Obtener la lista de gastos
            status_code, expenses = ExpenseService.get_family_expenses(family_id, telegram_id)
            
            if status_code >= 400 or not expenses:
                await update.message.reply_text(
                    Messages.ERROR_NO_EXPENSES,
                    reply_markup=Keyboards.get_main_menu_keyboard()
                )
                return ConversationHandler.END
            
            # Guardar los gastos en el contexto
            context.user_data["edit_data"]["expenses"] = expenses
            
            # Crear un teclado con los gastos
            keyboard = []
            for expense in expenses:
                description = expense.get("description", "Sin descripción")
                amount = expense.get("amount", 0)
                expense_id = expense.get("id", "")
                # Incluir el ID del gasto en el texto para poder identificarlo
                row = [f"{description} - ${amount:.2f} (ID: {expense_id})"]
                keyboard.append(row)
            
            # Añadir opción para volver
            keyboard.append(["↩️ Volver al Menú"])
            
            # Mostrar los gastos
            await update.message.reply_text(
                Messages.SELECT_EXPENSE_TO_EDIT,
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
            )
            return SELECT_EXPENSE
            
        elif option == "🗑️ Eliminar Gastos":
            # Obtener la lista de gastos
            status_code, expenses = ExpenseService.get_family_expenses(family_id, telegram_id)
            
            if status_code >= 400 or not expenses:
                await update.message.reply_text(
                    Messages.ERROR_NO_EXPENSES,
                    reply_markup=Keyboards.get_main_menu_keyboard()
                )
                return ConversationHandler.END
            
            # Guardar los gastos en el contexto
            context.user_data["edit_data"]["expenses"] = expenses
            
            # Crear un teclado con los gastos
            keyboard = []
            for expense in expenses:
                description = expense.get("description", "Sin descripción")
                amount = expense.get("amount", 0)
                expense_id = expense.get("id", "")
                # Incluir el ID del gasto en el texto para poder identificarlo
                row = [f"{description} - ${amount:.2f} (ID: {expense_id})"]
                keyboard.append(row)
            
            # Añadir opción para volver
            keyboard.append(["↩️ Volver al Menú"])
            
            # Mostrar los gastos
            await update.message.reply_text(
                Messages.SELECT_EXPENSE_TO_DELETE,
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
            )
            return SELECT_EXPENSE
            
        elif option == "📝 Editar Pagos":
            # Obtener la lista de pagos
            status_code, payments = PaymentService.get_family_payments(family_id)
            
            if status_code >= 400 or not payments:
                await update.message.reply_text(
                    Messages.ERROR_NO_PAYMENTS,
                    reply_markup=Keyboards.get_main_menu_keyboard()
                )
                return ConversationHandler.END
            
            # Guardar los pagos en el contexto
            context.user_data["edit_data"]["payments"] = payments
            
            # Obtener los nombres de los miembros
            member_names = context.user_data.get("member_names", {})
            
            # Crear un teclado con los pagos
            keyboard = []
            for payment in payments:
                from_member_id = payment.get("from_member", 0)
                to_member_id = payment.get("to_member", 0)
                amount = payment.get("amount", 0)
                payment_id = payment.get("id", "")
                
                from_name = member_names.get(str(from_member_id), f"Usuario {from_member_id}")
                to_name = member_names.get(str(to_member_id), f"Usuario {to_member_id}")
                
                # Incluir el ID del pago en el texto para poder identificarlo
                row = [f"{from_name} → {to_name} - ${amount:.2f} (ID: {payment_id})"]
                keyboard.append(row)
            
            # Añadir opción para volver
            keyboard.append(["↩️ Volver al Menú"])
            
            # Mostrar los pagos
            await update.message.reply_text(
                Messages.SELECT_PAYMENT_TO_EDIT,
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
            )
            return SELECT_PAYMENT
            
        elif option == "🗑️ Eliminar Pagos":
            # Obtener la lista de pagos
            status_code, payments = PaymentService.get_family_payments(family_id)
            
            if status_code >= 400 or not payments:
                await update.message.reply_text(
                    Messages.ERROR_NO_PAYMENTS,
                    reply_markup=Keyboards.get_main_menu_keyboard()
                )
                return ConversationHandler.END
            
            # Guardar los pagos en el contexto
            context.user_data["edit_data"]["payments"] = payments
            
            # Obtener los nombres de los miembros
            member_names = context.user_data.get("member_names", {})
            
            # Crear un teclado con los pagos
            keyboard = []
            for payment in payments:
                from_member_id = payment.get("from_member", 0)
                to_member_id = payment.get("to_member", 0)
                amount = payment.get("amount", 0)
                payment_id = payment.get("id", "")
                
                from_name = member_names.get(str(from_member_id), f"Usuario {from_member_id}")
                to_name = member_names.get(str(to_member_id), f"Usuario {to_member_id}")
                
                # Incluir el ID del pago en el texto para poder identificarlo
                row = [f"{from_name} → {to_name} - ${amount:.2f} (ID: {payment_id})"]
                keyboard.append(row)
            
            # Añadir opción para volver
            keyboard.append(["↩️ Volver al Menú"])
            
            # Mostrar los pagos
            await update.message.reply_text(
                Messages.SELECT_PAYMENT_TO_DELETE,
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
            )
            return SELECT_PAYMENT
            
        elif option == "↩️ Volver al Menú":
            # Mostrar el menú principal
            await update.message.reply_text(
                Messages.MAIN_MENU,
                reply_markup=Keyboards.get_main_menu_keyboard()
            )
            return ConversationHandler.END
            
        else:
            await update.message.reply_text(
                Messages.ERROR_INVALID_OPTION,
                reply_markup=Keyboards.get_edit_options_keyboard()
            )
            return EDIT_OPTION
    
    except Exception as e:
        print(f"Error en handle_edit_option: {str(e)}")
        traceback.print_exc()
        await send_error(update, context, str(e))
        return ConversationHandler.END

async def handle_select_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja la selección de un gasto para editar o eliminar."""
    try:
        selection = update.message.text
        
        if selection == "↩️ Volver al Menú":
            # Mostrar el menú principal
            await update.message.reply_text(
                Messages.MAIN_MENU,
                reply_markup=Keyboards.get_main_menu_keyboard()
            )
            return ConversationHandler.END
        
        # Buscar el gasto seleccionado
        expenses = context.user_data["edit_data"].get("expenses", [])
        selected_expense = None
        
        # Extraer el ID del gasto de la selección
        import re
        expense_id_match = re.search(r'\(ID: ([^)]+)\)', selection)
        expense_id = expense_id_match.group(1) if expense_id_match else None
        
        if expense_id:
            # Buscar el gasto por ID
            for expense in expenses:
                if str(expense.get("id")) == expense_id:
                    selected_expense = expense
                    break
        else:
            # Método anterior de búsqueda (por si acaso)
            for expense in expenses:
                description = expense.get("description", "Sin descripción")
                amount = expense.get("amount", 0)
                if selection.startswith(f"{description} - ${amount:.2f}"):
                    selected_expense = expense
                    break
        
        if not selected_expense:
            await update.message.reply_text(
                Messages.ERROR_EXPENSE_NOT_FOUND,
                reply_markup=Keyboards.get_main_menu_keyboard()
            )
            return ConversationHandler.END
        
        # Guardar el gasto seleccionado
        context.user_data["edit_data"]["selected_expense"] = selected_expense
        
        # Verificar la opción seleccionada
        option = context.user_data["edit_data"].get("option")
        
        if option == "📝 Editar Gastos":
            # Implementar la edición de gastos
            expense_id = selected_expense.get("id")
            description = selected_expense.get("description", "Sin descripción")
            amount = selected_expense.get("amount", 0)
            
            # Guardar el ID del gasto
            context.user_data["edit_data"]["expense_id"] = expense_id
            
            # Pedir el nuevo monto
            await update.message.reply_text(
                f"Vas a editar el gasto: *{description}*\n"
                f"Monto actual: *${amount:.2f}*\n\n"
                f"Por favor, ingresa el nuevo monto:",
                parse_mode="Markdown",
                reply_markup=Keyboards.get_cancel_keyboard()
            )
            return EDIT_EXPENSE_AMOUNT
            
        elif option == "🗑️ Eliminar Gastos":
            # Formatear los detalles del gasto
            expense_id = selected_expense.get("id")
            description = selected_expense.get("description", "Sin descripción")
            amount = selected_expense.get("amount", 0)
            
            details = (
                f"*Descripción:* {description}\n"
                f"*Monto:* ${amount:.2f}\n"
                f"*ID:* {expense_id}"
            )
            
            # Guardar el ID del gasto
            context.user_data["edit_data"]["expense_id"] = expense_id
            
            # Pedir confirmación
            await update.message.reply_text(
                Messages.CONFIRM_DELETE_EXPENSE.format(details=details),
                parse_mode="Markdown",
                reply_markup=Keyboards.get_confirmation_keyboard()
            )
            return CONFIRM_DELETE
    
    except Exception as e:
        print(f"Error en handle_select_expense: {str(e)}")
        traceback.print_exc()
        await send_error(update, context, str(e))
        return ConversationHandler.END

async def handle_edit_expense_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja la edición del monto de un gasto."""
    try:
        new_amount_text = update.message.text
        
        if new_amount_text == "❌ Cancelar":
            await update.message.reply_text(
                Messages.CANCEL_OPERATION,
                reply_markup=Keyboards.get_main_menu_keyboard()
            )
            return ConversationHandler.END
        
        # Validar que el monto sea un número válido
        try:
            new_amount = float(new_amount_text.replace('$', '').replace(',', '.'))
            if new_amount <= 0:
                raise ValueError("El monto debe ser positivo")
        except ValueError:
            await update.message.reply_text(
                Messages.ERROR_INVALID_AMOUNT,
                reply_markup=Keyboards.get_cancel_keyboard()
            )
            return EDIT_EXPENSE_AMOUNT
        
        # Obtener el gasto seleccionado
        selected_expense = context.user_data["edit_data"].get("selected_expense")
        expense_id = context.user_data["edit_data"].get("expense_id")
        
        if not selected_expense or not expense_id:
            await update.message.reply_text(
                Messages.ERROR_EXPENSE_NOT_FOUND,
                reply_markup=Keyboards.get_main_menu_keyboard()
            )
            return ConversationHandler.END
        
        # Actualizar el monto del gasto
        description = selected_expense.get("description", "Sin descripción")
        old_amount = selected_expense.get("amount", 0)
        
        # Crear los datos para la actualización
        update_data = {
            "amount": new_amount
        }
        
        # Llamar al servicio para actualizar el gasto
        status_code, response = ExpenseService.update_expense(expense_id, update_data)
        
        if status_code >= 400:
            await update.message.reply_text(
                f"❌ Error al actualizar el gasto: {response.get('detail', 'Error desconocido')}",
                reply_markup=Keyboards.get_main_menu_keyboard()
            )
            return ConversationHandler.END
        
        # Mostrar mensaje de éxito
        await update.message.reply_text(
            f"✅ Gasto actualizado con éxito:\n\n"
            f"*Descripción:* {description}\n"
            f"*Monto anterior:* ${old_amount:.2f}\n"
            f"*Nuevo monto:* ${new_amount:.2f}",
            parse_mode="Markdown",
            reply_markup=Keyboards.get_main_menu_keyboard()
        )
        
        # Limpiar datos
        if "edit_data" in context.user_data:
            del context.user_data["edit_data"]
        
        return ConversationHandler.END
    
    except Exception as e:
        print(f"Error en handle_edit_expense_amount: {str(e)}")
        traceback.print_exc()
        await send_error(update, context, str(e))
        return ConversationHandler.END

async def handle_select_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja la selección de un pago para editar o eliminar."""
    try:
        selection = update.message.text
        
        if selection == "↩️ Volver al Menú":
            # Mostrar el menú principal
            await update.message.reply_text(
                Messages.MAIN_MENU,
                reply_markup=Keyboards.get_main_menu_keyboard()
            )
            return ConversationHandler.END
        
        # Buscar el pago seleccionado
        payments = context.user_data["edit_data"].get("payments", [])
        member_names = context.user_data.get("member_names", {})
        selected_payment = None
        
        # Extraer el ID del pago de la selección
        import re
        payment_id_match = re.search(r'\(ID: ([^)]+)\)', selection)
        payment_id = payment_id_match.group(1) if payment_id_match else None
        
        if payment_id:
            # Buscar el pago por ID
            for payment in payments:
                if str(payment.get("id")) == payment_id:
                    selected_payment = payment
                    break
        else:
            # Método anterior de búsqueda (por si acaso)
            for payment in payments:
                from_member_id = payment.get("from_member", 0)
                to_member_id = payment.get("to_member", 0)
                amount = payment.get("amount", 0)
                
                from_name = member_names.get(str(from_member_id), f"Usuario {from_member_id}")
                to_name = member_names.get(str(to_member_id), f"Usuario {to_member_id}")
                
                if selection.startswith(f"{from_name} → {to_name} - ${amount:.2f}"):
                    selected_payment = payment
                    break
        
        if not selected_payment:
            await update.message.reply_text(
                Messages.ERROR_PAYMENT_NOT_FOUND,
                reply_markup=Keyboards.get_main_menu_keyboard()
            )
            return ConversationHandler.END
        
        # Guardar el pago seleccionado
        context.user_data["edit_data"]["selected_payment"] = selected_payment
        
        # Verificar la opción seleccionada
        option = context.user_data["edit_data"].get("option")
        
        if option == "📝 Editar Pagos":
            # TODO: Implementar la edición de pagos
            await update.message.reply_text(
                "La edición de pagos aún no está implementada.",
                reply_markup=Keyboards.get_main_menu_keyboard()
            )
            return ConversationHandler.END
            
        elif option == "🗑️ Eliminar Pagos":
            # Formatear los detalles del pago
            payment_id = selected_payment.get("id")
            from_member_id = selected_payment.get("from_member", 0)
            to_member_id = selected_payment.get("to_member", 0)
            amount = selected_payment.get("amount", 0)
            
            from_name = member_names.get(str(from_member_id), f"Usuario {from_member_id}")
            to_name = member_names.get(str(to_member_id), f"Usuario {to_member_id}")
            
            details = (
                f"*De:* {from_name}\n"
                f"*Para:* {to_name}\n"
                f"*Monto:* ${amount:.2f}\n"
                f"*ID:* {payment_id}"
            )
            
            # Guardar el ID del pago
            context.user_data["edit_data"]["payment_id"] = payment_id
            
            # Pedir confirmación
            await update.message.reply_text(
                Messages.CONFIRM_DELETE_PAYMENT.format(details=details),
                parse_mode="Markdown",
                reply_markup=Keyboards.get_confirmation_keyboard()
            )
            return CONFIRM_DELETE
    
    except Exception as e:
        print(f"Error en handle_select_payment: {str(e)}")
        traceback.print_exc()
        await send_error(update, context, str(e))
        return ConversationHandler.END

async def handle_confirm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja la confirmación de eliminación de un gasto o pago."""
    try:
        option = update.message.text
        
        if option == "❌ Cancelar":
            await update.message.reply_text(
                Messages.CANCEL_OPERATION,
                reply_markup=Keyboards.get_main_menu_keyboard()
            )
            return ConversationHandler.END
            
        elif option == "✅ Confirmar":
            # Verificar qué se está eliminando
            edit_option = context.user_data["edit_data"].get("option")
            
            if edit_option == "🗑️ Eliminar Gastos":
                # Eliminar el gasto
                expense_id = context.user_data["edit_data"].get("expense_id")
                status_code, response = ExpenseService.delete_expense(expense_id)
                
                if status_code >= 400:
                    await update.message.reply_text(
                        Messages.ERROR_DELETING_EXPENSE,
                        reply_markup=Keyboards.get_main_menu_keyboard()
                    )
                    return ConversationHandler.END
                
                # Mostrar mensaje de éxito
                await update.message.reply_text(
                    Messages.SUCCESS_EXPENSE_DELETED,
                    reply_markup=Keyboards.get_main_menu_keyboard()
                )
                
            elif edit_option == "🗑️ Eliminar Pagos":
                # Eliminar el pago
                payment_id = context.user_data["edit_data"].get("payment_id")
                status_code, response = PaymentService.delete_payment(payment_id)
                
                if status_code >= 400:
                    await update.message.reply_text(
                        Messages.ERROR_DELETING_PAYMENT,
                        reply_markup=Keyboards.get_main_menu_keyboard()
                    )
                    return ConversationHandler.END
                
                # Mostrar mensaje de éxito
                await update.message.reply_text(
                    Messages.SUCCESS_PAYMENT_DELETED,
                    reply_markup=Keyboards.get_main_menu_keyboard()
                )
            
            # Limpiar datos
            if "edit_data" in context.user_data:
                del context.user_data["edit_data"]
            
            return ConversationHandler.END
            
        else:
            await update.message.reply_text(
                Messages.ERROR_INVALID_OPTION,
                reply_markup=Keyboards.get_confirmation_keyboard()
            )
            return CONFIRM_DELETE
    
    except Exception as e:
        print(f"Error en handle_confirm_delete: {str(e)}")
        traceback.print_exc()
        await send_error(update, context, str(e))
        return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancela la operación actual."""
    await update.message.reply_text(
        Messages.CANCEL_OPERATION,
        reply_markup=Keyboards.get_main_menu_keyboard()
    )
    
    # Limpiar datos
    if "edit_data" in context.user_data:
        del context.user_data["edit_data"]
    
    return ConversationHandler.END 