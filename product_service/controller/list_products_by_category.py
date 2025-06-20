import os
import json
from boto3.dynamodb.conditions import Key
from infrastructure.dynamodb_client import products_table
from infrastructure.jwt_validator import verify_jwt, UnauthorizedError
from dto.product_dto import ProductDTO  # Importamos el DTO para productos

def lambda_handler(event, context):
    # 1. Verificar JWT
    try:
        verify_jwt(event)
    except UnauthorizedError as e:
        return {
            'statusCode': 401,
            'body': json.dumps({'message': str(e)})
        }

    # 2. Leer parámetros de consulta
    params = event.get('queryStringParameters') or {}
    category = params.get('category')  # Usamos 'category' como string (nombre de la categoría)
    if not category:
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Falta parámetro category'})
        }

    try:
        limit = int(params.get('limit', '10'))
    except ValueError:
        limit = 10

    last_key = params.get('lastKey')

    # 3. Construir argumentos de query
    query_kwargs = {
        'IndexName': 'CategoryIndex',  # GSI sobre category (nombre de la categoría)
        'KeyConditionExpression': Key('category').eq(category),  # Usamos 'category' en lugar de 'category_id'
        'Limit': limit
    }
    if last_key:
        query_kwargs['ExclusiveStartKey'] = json.loads(last_key)

    # 4. Ejecutar query en DynamoDB
    try:
        response = products_table.query(**query_kwargs)
        items = response.get('Items', [])
        last_evaluated_key = response.get('LastEvaluatedKey')

        # Convertir los productos a DTOs
        product_dtos = [ProductDTO.from_domain(item) for item in items]

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Error leyendo productos', 'error': str(e)})
        }

    # 5. Devolver resultados y la key para la siguiente página en formato DTO
    body = {
        'products': [product.to_dict() for product in product_dtos],  # Usamos to_dict para convertir a JSON
        'lastKey': json.dumps(last_evaluated_key) if last_evaluated_key else None
    }

    return {
        'statusCode': 200,
        'body': json.dumps(body)
    }
