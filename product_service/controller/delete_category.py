import json
from infrastructure.dynamodb_client import categories_table
from infrastructure.jwt_validator import verify_jwt, UnauthorizedError
from dto.category_dto import CategoryDTO  # Importar el DTO para usar en la respuesta

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

    # 3. Eliminar de DynamoDB
    try:
        # Primero obtenemos la categoría antes de eliminarla (para confirmar si existe)
        response = categories_table.get_item(Key={'id_categoria': int(cat_id)})
        item = response.get('Item')

        if not item:
            return {
                'statusCode': 404,
                'body': json.dumps({'message': 'Categoría no encontrada'})
            }

        # Procedemos a eliminar la categoría
        categories_table.delete_item(Key={'id_categoria': int(cat_id)})

        # Convertir la categoría eliminada a DTO para la respuesta
        category_dto = CategoryDTO.from_domain(item)  # Usamos el DTO para formatear la respuesta

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Error eliminando categoría', 'error': str(e)})
        }

    # 4. Confirmación: Devolvemos el DTO con el mensaje de eliminación
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Categoría eliminada',
            'category': category_dto.to_dict()  # Devolvemos el DTO de la categoría eliminada
        })
    }
