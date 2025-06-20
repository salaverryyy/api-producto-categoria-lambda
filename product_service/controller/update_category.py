import json
from infrastructure.dynamodb_client import categories_table
from infrastructure.jwt_validator import verify_jwt, UnauthorizedError
from dto.category_dto import CategoryDTO  # Importamos el DTO

def lambda_handler(event, context):
    # 1. Verificar JWT
    try:
        verify_jwt(event)
    except UnauthorizedError as e:
        return {
            'statusCode': 401,
            'body': json.dumps({'message': str(e)})
        }

    # 2. Leer id de pathParameters
    path = event.get('pathParameters') or {}
    cat_id = path.get('id')
    if not cat_id:
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Falta parámetro id'})
        }

    # 3. Parsear body y preparar actualización
    body = json.loads(event.get('body') or '{}')
    allowed = ['nombre', 'descripcion']
    expr = []
    names  = {}
    values = {}
    
    # Convertir el body a CategoryDTO
    category_dto = CategoryDTO.from_dict(body)

    for field in allowed:
        if field in body:
            expr.append(f"#{field} = :{field}")
            names[f"#{field}"]  = field
            val = body[field]
            if field == 'nombre':
                val = category_dto.nombre
            elif field == 'descripcion':
                val = category_dto.descripcion
            values[f":{field}"] = val

    if not expr:
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'No hay campos para actualizar'})
        }

    update_expr = "SET " + ", ".join(expr)

    # 4. Ejecutar update
    try:
        resp = categories_table.update_item(
            Key={'id_categoria': int(cat_id)},  # Usamos el id_categoria para la actualización
            UpdateExpression=update_expr,
            ExpressionAttributeNames=names,
            ExpressionAttributeValues=values,
            ReturnValues='ALL_NEW'
        )
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Error modificando categoría', 'error': str(e)})
        }

    updated = resp.get('Attributes', {})
    updated_dto = CategoryDTO.from_domain(updated)  # Convertir el resultado a un DTO

    # 5. Devolver el DTO actualizado como respuesta
    return {
        'statusCode': 200,
        'body': json.dumps(updated_dto.to_dict())  # Devolver el DTO como parte de la respuesta
    }
