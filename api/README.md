# API de Family Finance

Esta API proporciona los servicios necesarios para gestionar las finanzas familiares, incluyendo la creación de familias, miembros, gastos y pagos.

## Requisitos

- Python 3.8+
- PostgreSQL

## Instalación

1. Clonar el repositorio:

```bash
git clone <url-del-repositorio>
cd <directorio-del-repositorio>/api
```

2. Crear un entorno virtual:

```bash
python -m venv env
source env/bin/activate  # En Windows: env\Scripts\activate
```

3. Instalar las dependencias:

```bash
pip install -r requirements.txt
```

4. Configurar las variables de entorno:

Crea un archivo `.env` en el directorio `api` con el siguiente contenido:

```
# Configuración de la base de datos
DATABASE_URL=postgresql://usuario:contraseña@localhost/familyfinance

# Configuración de seguridad
SECRET_KEY=tu_clave_secreta
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Configuración de la API
API_PORT=8007
API_HOST=0.0.0.0
```

5. Crear la base de datos:

```bash
createdb familyfinance
```

## Ejecución

Para ejecutar la API:

```bash
python run.py
```

La API estará disponible en `http://localhost:8007`.

## Documentación

La documentación de la API estará disponible en `http://localhost:8007/docs`.

## Endpoints

### Autenticación

- `POST /auth/token`: Obtiene un token de acceso.

### Familias

- `POST /families/`: Crea una nueva familia.
- `GET /families/{family_id}`: Obtiene información de una familia.
- `GET /families/{family_id}/members`: Obtiene los miembros de una familia.
- `POST /families/{family_id}/members`: Añade un miembro a una familia.
- `GET /families/{family_id}/balances`: Obtiene los balances de una familia.

### Miembros

- `GET /members/{telegram_id}`: Obtiene un miembro por su ID de Telegram.
- `GET /members/me`: Obtiene el miembro actual.
- `GET /members/me/balance`: Obtiene el balance del miembro actual.
- `PUT /members/{member_id}`: Actualiza un miembro.
- `DELETE /members/{member_id}`: Elimina un miembro.

### Gastos

- `POST /expenses/`: Crea un nuevo gasto.
- `GET /expenses/{expense_id}`: Obtiene un gasto por su ID.
- `GET /expenses/family/{family_id}`: Obtiene los gastos de una familia.
- `DELETE /expenses/{expense_id}`: Elimina un gasto.

### Pagos

- `POST /payments/`: Crea un nuevo pago.
- `GET /payments/{payment_id}`: Obtiene un pago por su ID.
- `GET /payments/family/{family_id}`: Obtiene los pagos de una familia.
- `DELETE /payments/{payment_id}`: Elimina un pago. 