import json
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

    # 3. Obtener el producto antes de eliminarlo
    try:
        response = products_table.get_item(Key={'id_producto': int(prod_id)})
        item = response.get('Item')

        if not item:
            return {
                'statusCode': 404,
                'body': json.dumps({'message': 'Producto no encontrado'})
            }

        # Eliminar el producto de DynamoDB
        products_table.delete_item(Key={'id_producto': int(prod_id)})

        # Convertir el producto eliminado en un DTO
        product_dto = ProductDTO.from_domain(item)  # Usamos el DTO para formatear la respuesta

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Error eliminando producto', 'error': str(e)})
        }

    # 4. Confirmación: Devolvemos el DTO con el producto eliminado
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Producto eliminado',
            'product': product_dto.to_dict()  # Devolvemos el DTO de la categoría eliminada
        })
    }
