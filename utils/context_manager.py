from telegram.ext import ContextTypes
from services.family_service import FamilyService
from services.member_service import MemberService
from services.auth_service import AuthService
import traceback

class ContextManager:
    """Gestor de contexto para manejar los datos del usuario."""
    
    @staticmethod
    async def check_user_in_family(context: ContextTypes.DEFAULT_TYPE, telegram_id: str):
        """Verifica si el usuario está en una familia y guarda el ID en el contexto.
        
        Args:
            context: Contexto de Telegram
            telegram_id: ID de Telegram del usuario
            
        Returns:
            bool: True si el usuario está en una familia, False en caso contrario
        """
        # Si ya tenemos el family_id en el contexto, no necesitamos verificar
        if "family_id" in context.user_data:
            print(f"Usuario ya tiene family_id en el contexto: {context.user_data['family_id']}")
            return True
        
        # Verificar si el usuario está en una familia
        print(f"Verificando si el usuario {telegram_id} está en una familia con la API")
        try:
            # Guardar el ID de Telegram en el contexto para usarlo como identificación
            context.user_data["telegram_id"] = telegram_id
            
            # Obtener información del miembro directamente
            status_code, response = MemberService.get_member(telegram_id)
            
            print(f"Respuesta de get_member: status_code={status_code}, response={response}")
            
            if status_code == 200 and response and response.get("family_id"):
                # Guardar el ID de la familia en el contexto
                family_id = response.get("family_id")
                context.user_data["family_id"] = family_id
                print(f"ID de familia guardado en el contexto: {family_id}")
                return True
            
            print("Usuario no está en ninguna familia según la API")
            return False
        except Exception as e:
            print(f"Error en check_user_in_family: {str(e)}")
            traceback.print_exc()
            return False
    
    @staticmethod
    async def load_family_members(context: ContextTypes.DEFAULT_TYPE, family_id: str):
        """Carga los miembros de la familia en el contexto.
        
        Args:
            context: Contexto de Telegram
            family_id: ID de la familia
            
        Returns:
            bool: True si se cargaron los miembros correctamente, False en caso contrario
        """
        print(f"Cargando miembros de la familia {family_id}")
        
        try:
            # Obtener el ID de Telegram del contexto
            telegram_id = context.user_data.get("telegram_id")
            
            # Obtener información de la familia
            status_code, family = FamilyService.get_family(family_id, telegram_id)
            print(f"Respuesta de get_family: status_code={status_code}, family={family}")
            
            if status_code == 200 and family and "members" in family:
                # Guardar la familia completa en el contexto
                context.user_data["family_info"] = family
                print(f"Familia guardada en el contexto: {family}")
                
                # Crear y guardar un diccionario de ID -> nombre para facilitar la búsqueda
                member_names = {}
                print(f"Miembros encontrados: {len(family['members'])}")
                
                for member in family["members"]:
                    member_id = member.get("id", "")
                    member_name = member.get("name", f"Usuario {member_id}")
                    telegram_id = member.get("telegram_id", "")
                    
                    print(f"Miembro: id={member_id}, name={member_name}, telegram_id={telegram_id}")
                    
                    # Guardar por ID como string (para asegurar compatibilidad)
                    member_names[str(member_id)] = member_name
                    
                    # También guardar por ID numérico si es posible
                    if isinstance(member_id, int) or (isinstance(member_id, str) and member_id.isdigit()):
                        member_names[int(member_id)] = member_name
                    
                    # También guardar versiones con prefijos para mayor compatibilidad
                    member_names[f"Usuario {member_id}"] = member_name
                    
                    # Si tenemos el telegram_id, también guardarlo
                    if telegram_id:
                        member_names[telegram_id] = member_name
                
                context.user_data["member_names"] = member_names
                print(f"Nombres de miembros guardados en el contexto: {member_names}")
                return True
            else:
                print(f"Error al cargar miembros: status_code={status_code}, family={family}")
                return False
        except Exception as e:
            print(f"Error en load_family_members: {str(e)}")
            traceback.print_exc()
            return False
    
    @staticmethod
    def get_family_id(context: ContextTypes.DEFAULT_TYPE):
        """Obtiene el ID de la familia del contexto.
        
        Args:
            context: Contexto de Telegram
            
        Returns:
            str: ID de la familia o None si no está disponible
        """
        return context.user_data.get("family_id")
    
    @staticmethod
    def get_member_names(context: ContextTypes.DEFAULT_TYPE):
        """Obtiene el diccionario de nombres de miembros del contexto.
        
        Args:
            context: Contexto de Telegram
            
        Returns:
            dict: Diccionario de ID -> nombre o un diccionario vacío si no está disponible
        """
        return context.user_data.get("member_names", {})
    
    @staticmethod
    def get_telegram_id(context: ContextTypes.DEFAULT_TYPE):
        """Obtiene el ID de Telegram del contexto.
        
        Args:
            context: Contexto de Telegram
            
        Returns:
            str: ID de Telegram o None si no está disponible
        """
        return context.user_data.get("telegram_id")
    
    @staticmethod
    def clear_context(context: ContextTypes.DEFAULT_TYPE, keys=None):
        """Limpia el contexto del usuario.
        
        Args:
            context: Contexto de Telegram
            keys: Lista de claves a limpiar (si es None, limpia todo)
        """
        if keys is None:
            context.user_data.clear()
        else:
            for key in keys:
                if key in context.user_data:
                    del context.user_data[key] 