import json
from decimal import Decimal
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

    # 2. Leer productId de pathParameters
    path = event.get('pathParameters') or {}
    prod_id = path.get('id')
    if not prod_id:
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Falta parámetro id'})
        }

    # 3. Parsear body y filtrar sólo campos permitidos
    body = json.loads(event.get('body') or '{}')
    allowed_fields = [
        'nombre', 'direccion', 'precio', 'stock',
        'imagen_url', 'fecha_creacion', 'proveedor', 'category'
    ]

    update_clauses = []
    expr_attr_names  = {}
    expr_attr_values = {}

    for field in allowed_fields:
        if field in body:
            update_clauses.append(f"#{field} = :{field}")
            expr_attr_names[f"#{field}"]  = field
            val = body[field]
            if field == 'precio':
                val = Decimal(str(val))
            expr_attr_values[f":{field}"] = val

    if not update_clauses:
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'No hay campos para actualizar'})
        }

    update_expr = "SET " + ", ".join(update_clauses)

    # 4. Ejecutar update_item en DynamoDB
    try:
        resp = products_table.update_item(
            Key={'id_producto': int(prod_id)},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_attr_names,
            ExpressionAttributeValues=expr_attr_values,
            ReturnValues='ALL_NEW'
        )
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Error actualizando producto', 'error': str(e)})
        }

    updated = resp.get('Attributes', {})
    
    # Convertir la respuesta de DynamoDB en un DTO antes de devolverla
    updated_dto = ProductDTO.from_domain(updated)  # Convertimos la respuesta a un ProductDTO

    # Devolver el DTO actualizado como respuesta
    return {
        'statusCode': 200,
        'body': json.dumps(updated_dto.to_dict())  # Devolvemos el DTO como parte de la respuesta
    }
