from services.api_service import ApiService
import traceback

class FamilyService:
    """Servicio para interactuar con familias."""
    
    @staticmethod
    def create_family(name, members, token=None):
        """Crea una nueva familia.
        
        Args:
            name: Nombre de la familia
            members: Lista de miembros iniciales
            token: Token de autenticación (opcional)
            
        Returns:
            tuple: (status_code, response)
        """
        print(f"Creando familia con nombre '{name}' y miembros: {members}")
        data = {
            "name": name,
            "members": members
        }
        status_code, response = ApiService.request("POST", "/families/", data, token=token, check_status=False)
        print(f"Respuesta de create_family: status_code={status_code}, response={response}")
        return status_code, response
    
    @staticmethod
    def get_family(family_id, token=None):
        """Obtiene información de una familia.
        
        Args:
            family_id: ID de la familia
            token: Token de autenticación (opcional)
            
        Returns:
            tuple: (status_code, response)
        """
        print(f"Obteniendo información de la familia con ID: {family_id}")
        status_code, response = ApiService.request("GET", f"/families/{family_id}", token=token, check_status=False)
        print(f"Respuesta de get_family: status_code={status_code}, response={response}")
        return status_code, response
    
    @staticmethod
    def get_family_members(family_id, token=None):
        """Obtiene los miembros de una familia.
        
        Args:
            family_id: ID de la familia
            token: Token de autenticación (opcional)
            
        Returns:
            tuple: (status_code, response)
        """
        print(f"Obteniendo miembros de la familia con ID: {family_id}")
        status_code, response = ApiService.request("GET", f"/families/{family_id}/members", token=token, check_status=False)
        print(f"Respuesta de get_family_members: status_code={status_code}, response={response}")
        return status_code, response
    
    @staticmethod
    def add_member_to_family(family_id, telegram_id, name, token=None):
        """Añade un miembro a una familia.
        
        Args:
            family_id: ID de la familia
            telegram_id: ID de Telegram del miembro
            name: Nombre del miembro
            token: Token de autenticación (opcional)
            
        Returns:
            tuple: (status_code, response)
        """
        print(f"Añadiendo miembro a la familia {family_id}: telegram_id={telegram_id}, name={name}")
        data = {
            "telegram_id": telegram_id,
            "name": name
        }
        status_code, response = ApiService.request("POST", f"/families/{family_id}/members", data, token=token, check_status=False)
        print(f"Respuesta de add_member_to_family: status_code={status_code}, response={response}")
        return status_code, response
    
    @staticmethod
    def get_family_balances(family_id, token=None):
        """Obtiene los balances de una familia.
        
        Args:
            family_id: ID de la familia
            token: Token de autenticación (opcional)
            
        Returns:
            tuple: (status_code, response)
        """
        try:
            print(f"Solicitando balances para la familia {family_id}")
            status_code, response = ApiService.request("GET", f"/families/{family_id}/balances", token=token, check_status=False)
            print(f"Respuesta de get_family_balances: status_code={status_code}, response={response}")
            
            # Verificar si la respuesta es válida
            if status_code >= 400:
                print(f"Error al obtener balances: status_code={status_code}, response={response}")
                return status_code, response
                
            # Verificar si la respuesta es una lista o un diccionario
            if not isinstance(response, list) and not isinstance(response, dict):
                print(f"Respuesta de balances no es una lista ni un diccionario: {response}")
                return status_code, []
                
            return status_code, response
        except Exception as e:
            print(f"Error en get_family_balances: {str(e)}")
            traceback.print_exc()
            return 500, {"error": f"Error al obtener balances: {str(e)}"} 