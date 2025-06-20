import json
from infrastructure.dynamodb_client import categories_table
from infrastructure.jwt_validator import verify_jwt, UnauthorizedError
from dto.category_dto import CategoryDTO  # Importa el DTO

def lambda_handler(event, context):
    # 1. Verificar JWT
    try:
        verify_jwt(event)
    except UnauthorizedError as e:
        return {
            'statusCode': 401,
            'body': json.dumps({'message': str(e)})
        }

    # 2. Parsear body
    body = json.loads(event.get('body') or '{}')
    required = ['id_categoria', 'nombre', 'descripcion']
    if not all(k in body for k in required):
        return {
            'statusCode': 400,
            'body': json.dumps({'message': f'Faltan campos: {required}'})
        }

    # 3. Convertir los datos a CategoryDTO
    category_dto = CategoryDTO.from_dict(body)

    # 4. Insertar en DynamoDB
    try:
        categories_table.put_item(Item=category_dto.to_dict())  # Insertar el DTO transformado
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Error creando categoría', 'error': str(e)})
        }

    # 5. Devolver el DTO actualizado como respuesta
    return {
        'statusCode': 201,
        'body': json.dumps(category_dto.to_dict())  # Devolvemos el DTO como parte de la respuesta
    }
