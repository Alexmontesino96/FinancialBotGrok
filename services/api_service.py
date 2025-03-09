import requests
import traceback
from config import API_BASE_URL

class ApiService:
    """Servicio base para interactuar con la API."""
    
    @staticmethod
    def request(method, endpoint, data=None, token=None, check_status=True):
        """Realiza una solicitud HTTP a la API.
        
        Args:
            method: Método HTTP (GET, POST, PUT, DELETE)
            endpoint: Endpoint de la API
            data: Datos a enviar en la solicitud (opcional)
            token: Token de autenticación o ID de Telegram (opcional)
            check_status: Si es True, lanza una excepción si el status code es un error
            
        Returns:
            tuple: (status_code, response_data)
        """
        # Asegurarse de que el endpoint comience con una barra diagonal
        if not endpoint.startswith('/'):
            endpoint = '/' + endpoint
            
        url = f"{API_BASE_URL}{endpoint}"
        print(f"Realizando solicitud {method} a {url}")
        if data:
            print(f"Datos: {data}")
            
        try:
            # Configurar headers para JSON
            headers = {'Content-Type': 'application/json'}
            
            # Añadir identificación si está disponible
            # En lugar de usar un token JWT, simplemente pasamos el ID de Telegram
            # como un parámetro de consulta o en los datos
            params = {}
            if token and isinstance(token, str):
                # Usar el token como ID de Telegram en un parámetro de consulta
                params['telegram_id'] = token
                print(f"Incluyendo telegram_id={token} en la solicitud")
            
            if method == "GET":
                response = requests.get(url, params=params, headers=headers, timeout=15)
            elif method == "POST":
                # Para solicitudes POST, solo incluir el telegram_id en los parámetros de consulta
                # y no duplicarlo en el cuerpo de la solicitud
                response = requests.post(url, json=data, params=params, headers=headers, timeout=15)
            elif method == "PUT":
                # Para solicitudes PUT, solo incluir el telegram_id en los parámetros de consulta
                # y no duplicarlo en el cuerpo de la solicitud
                response = requests.put(url, json=data, params=params, headers=headers, timeout=15)
            elif method == "DELETE":
                response = requests.delete(url, params=params, headers=headers, timeout=15)
            else:
                print(f"Método HTTP no soportado: {method}")
                return 400, {"error": f"Método HTTP no soportado: {method}"}
            
            # Obtener el status code
            status_code = response.status_code
            print(f"Status code: {status_code}")
            
            # Intentar obtener el contenido como JSON
            try:
                if response.content:
                    response_data = response.json()
                else:
                    response_data = {}
            except ValueError:
                print(f"Respuesta no es JSON válido: {response.content}")
                response_data = {"error": "Respuesta no es JSON válido", "content": str(response.content)}
            
            # Verificar si hubo un error
            if check_status and status_code >= 400:
                error_message = response_data.get("detail", "Error desconocido")
                print(f"Error en la solicitud: {error_message}")
                
            return status_code, response_data
            
        except requests.exceptions.ConnectionError as e:
            print(f"Error de conexión: {e}")
            traceback.print_exc()
            return 503, {"error": f"Error de conexión: {str(e)}"}
        except requests.exceptions.Timeout as e:
            print(f"Timeout en la solicitud: {e}")
            traceback.print_exc()
            return 504, {"error": f"Timeout en la solicitud: {str(e)}"}
        except Exception as e:
            print(f"Error inesperado: {e}")
            traceback.print_exc()
            return 500, {"error": f"Error inesperado: {str(e)}"}
            
    @staticmethod
    def api_request(method, endpoint, data=None, token=None, check_status=True):
        """Alias para request para mantener compatibilidad."""
        return ApiService.request(method, endpoint, data, token, check_status)