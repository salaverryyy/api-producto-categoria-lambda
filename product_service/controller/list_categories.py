import json
from infrastructure.dynamodb_client import categories_table
from infrastructure.jwt_validator import verify_jwt, UnauthorizedError
from dto.category_dto import CategoryDTO  # Importamos el DTO para categorías

def lambda_handler(event, context):
    # 1. Verificar JWT
    try:
        verify_jwt(event)
    except UnauthorizedError as e:
        return {
            'statusCode': 401,
            'body': json.dumps({'message': str(e)})
        }

    # 2. Listar todas las categorías
    try:
        response = categories_table.scan()
        items = response.get('Items', [])

        # Convertir las categorías a DTOs
        category_dtos = [CategoryDTO.from_domain(item) for item in items]

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Error leyendo categorías', 'error': str(e)})
        }

    # 3. Devolver listado de categorías en formato DTO
    return {
        'statusCode': 200,
        'body': json.dumps({'categories': [category.to_dict() for category in category_dtos]})
    }
