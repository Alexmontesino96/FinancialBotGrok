from services.api_service import ApiService
import traceback

class ExpenseService:
    """Servicio para interactuar con gastos."""
    
    @staticmethod
    def create_expense(description, amount, paid_by, telegram_id=None):
        """Crea un nuevo gasto.
        
        Args:
            description: Descripción del gasto
            amount: Monto del gasto
            paid_by: ID del miembro que pagó
            telegram_id: ID de Telegram del usuario que crea el gasto (opcional)
            
        Returns:
            tuple: (status_code, response)
        """
        try:
            print(f"Creando gasto: description={description}, amount={amount}, paid_by={paid_by}, telegram_id={telegram_id}")
            data = {
                "description": description,
                "amount": amount,
                "paid_by": paid_by
            }
            status_code, response = ApiService.request("POST", "/expenses", data, token=telegram_id, check_status=False)
            print(f"Resultado de create_expense: status_code={status_code}, response={response}")
            
            # Verificar si la respuesta es válida
            if status_code in [200, 201] and response:
                print(f"Gasto creado exitosamente: {response}")
                return status_code, response
            else:
                print(f"Error al crear gasto: status_code={status_code}, response={response}")
                return status_code, response
        except Exception as e:
            print(f"Excepción en create_expense: {str(e)}")
            traceback.print_exc()
            return 500, {"error": f"Error al crear gasto: {str(e)}"}
    
    @staticmethod
    def get_family_expenses(family_id, telegram_id=None):
        """Obtiene los gastos de una familia.
        
        Args:
            family_id: ID de la familia (UUID como string) 
            telegram_id: ID de Telegram del usuario (opcional)
            
        Returns:
            tuple: (status_code, response)
        """
        print(f"Obteniendo gastos para la familia con ID: {family_id}, telegram_id: {telegram_id}")
        
        # Verificar que family_id sea un valor válido
        if not family_id:
            print("Error: family_id es None o vacío")
            return 400, {"error": "ID de familia no válido"}
        
        # Ya no necesitamos convertir family_id a entero, ahora es un UUID como string
        
        # Llamar a la API con el ID de Telegram si está disponible
        return ApiService.request("GET", f"/expenses/family/{family_id}", token=telegram_id, check_status=False)
    
    @staticmethod
    def get_expense(expense_id):
        """Obtiene información de un gasto.
        
        Args:
            expense_id: ID del gasto (UUID como string)
            
        Returns:
            tuple: (status_code, response)
        """
        return ApiService.request("GET", f"/expenses/{expense_id}", check_status=False)
    
    @staticmethod
    def update_expense(expense_id, data, telegram_id=None):
        """Actualiza un gasto existente.
        
        Args:
            expense_id: ID del gasto (UUID como string)
            data: Datos a actualizar (diccionario)
            telegram_id: ID de Telegram del usuario (opcional)
            
        Returns:
            tuple: (status_code, response)
        """
        try:
            print(f"Actualizando gasto con ID: {expense_id}, datos: {data}, telegram_id: {telegram_id}")
            
            # Usar el endpoint PUT para actualizar el gasto
            status_code, response = ApiService.request("PUT", f"/expenses/{expense_id}", data, token=telegram_id, check_status=False)
            print(f"Resultado de update_expense: status_code={status_code}, response={response}")
            
            if status_code >= 400:
                print(f"Error al actualizar gasto: status_code={status_code}, response={response}")
            
            return status_code, response
        except Exception as e:
            print(f"Excepción en update_expense: {str(e)}")
            traceback.print_exc()
            return 500, {"error": f"Error al actualizar gasto: {str(e)}"}
    
    @staticmethod
    def delete_expense(expense_id):
        """Elimina un gasto.
        
        Args:
            expense_id: ID del gasto (UUID como string)
            
        Returns:
            tuple: (status_code, response)
        """
        return ApiService.request("DELETE", f"/expenses/{expense_id}", check_status=False) 