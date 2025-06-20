import json
from infrastructure.dynamodb_client import products_table
from infrastructure.jwt_validator import verify_jwt, UnauthorizedError
from dto.product_dto import ProductDTO  # Importamos el DTO para productos
from decimal import Decimal  # Asegúrate de importar Decimal para manejar precios

def lambda_handler(event, context):
    # 1. Verificar JWT
    try:
        verify_jwt(event)
    except UnauthorizedError as e:
        return {
            'statusCode': 401,
            'body': json.dumps({'message': str(e)})
        }

    # 2. Parsear el body y validar campos
    body = json.loads(event.get('body') or '{}')
    required = ['id_producto', 'nombre', 'direccion', 'precio', 'stock', 'proveedor', 'category']
    if not all(k in body for k in required):
        return {
            'statusCode': 400,
            'body': json.dumps({'message': f'Faltan campos: {required}'})
        }

    # 3. Convertir los datos a ProductDTO
    product_dto = ProductDTO.from_dict(body)

    # 4. Insertar en DynamoDB
    try:
        # Insertamos el producto en DynamoDB usando el DTO
        products_table.put_item(Item=product_dto.to_dict())
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Error creando producto', 'error': str(e)})
        }

    # 5. Devolver el DTO actualizado como respuesta
    return {
        'statusCode': 201,
        'body': json.dumps(product_dto.to_dict())  # Devolvemos el DTO como parte de la respuesta
    }
