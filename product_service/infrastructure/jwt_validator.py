import os
import jwt

JWT_SECRET = os.environ['JWT_SECRET']  # Defínelo en tu Lambda

class UnauthorizedError(Exception):
    pass

def verify_jwt(event):
    """
    Extrae y valida el token JWT de Authorization header.
    Lanza UnauthorizedError si falla.
    """
    headers = event.get('headers') or {}
    auth = headers.get('Authorization', '')
    parts = auth.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        raise UnauthorizedError('Formato de Authorization inválido')
    token = parts[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
    except jwt.PyJWTError as e:
        raise UnauthorizedError('Token inválido') from e
    return payload
