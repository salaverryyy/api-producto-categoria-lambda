import json
import boto3
import os

# Crear un cliente DynamoDB
dynamodb = boto3.resource('dynamodb')
product_table_name = os.getenv('PRODUCTS_TABLE')  # Usamos la variable de entorno para el nombre de la tabla de productos
category_table_name = os.getenv('PRODUCT_CATEGORY_TABLE')  # Usamos la variable de entorno para el nombre de la tabla de producto_categoria

product_table = dynamodb.Table(product_table_name)
category_table = dynamodb.Table(category_table_name)

# Nombre del Lambda de verificación de token
VERIFY_TOKEN_LAMBDA = os.getenv('VERIFY_TOKEN_LAMBDA')  # El nombre del Lambda verificar_token.py

def lambda_handler(event, context):
    try:
        # Obtener el token del encabezado Authorization
        auth_header = event['headers'].get('Authorization')
        if not auth_header:
            return {'statusCode': 401, 'body': json.dumps({'message': 'Token no proporcionado'})}

        token = auth_header.split(" ")[1]

        # Invocar el Lambda de verificación de token
        lambda_client = boto3.client('lambda')
        payload_string = json.dumps({'token': token})

        invoke_response = lambda_client.invoke(
            FunctionName=VERIFY_TOKEN_LAMBDA,
            InvocationType='RequestResponse',
            Payload=payload_string
        )

        # Procesar la respuesta del Lambda de verificación de token
        response = json.loads(invoke_response['Payload'].read().decode("utf-8"))

        if response['statusCode'] != 200:
            return {'statusCode': 403, 'body': json.dumps({'message': 'Acceso no autorizado'})}

        # Si el token es válido, continuar con la lógica para obtener los productos por categoría
        body = json.loads(event['body'])
        id_categoria = body['id_categoria']  # ID de la categoría para la que queremos listar los productos

        # Query para obtener todos los productos asociados a la categoría en ProductCategory
        response = category_table.query(
            KeyConditionExpression='id_categoria = :categoria_val',
            ExpressionAttributeValues={':categoria_val': id_categoria}
        )

        product_ids = [item['id_producto'] for item in response.get('Items', [])]  # Extraemos los ids de productos

        if not product_ids:
            return {
                'statusCode': 404,
                'body': json.dumps({'message': 'No se encontraron productos para esta categoría'})
            }

        # Ahora, buscamos los productos en la tabla Products usando `query`
        # Usamos `query` para obtener solo los productos que coinciden con `product_ids`
        products_response = product_table.query(
            KeyConditionExpression='id_producto IN (' + ','.join([f':id{i}' for i in range(len(product_ids))]) + ')',
            ExpressionAttributeValues={f':id{i}': product_ids[i] for i in range(len(product_ids))}
        )

        productos = products_response.get('Items', [])

        return {
            'statusCode': 200,
            'body': json.dumps({'productos': productos})
        }

    except Exception as e:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': str(e)})
        }
