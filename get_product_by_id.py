import json
import boto3
import os

# Crear un cliente DynamoDB
dynamodb = boto3.resource('dynamodb')
table_name = os.getenv('PRODUCTS_TABLE')  # Usamos la variable de entorno para el nombre de la tabla de productos
table = dynamodb.Table(table_name)

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

        # Si el token es válido, continuar con la obtención del producto por id_producto
        body = json.loads(event['body'])
        id_producto = body['id_producto']  # ID del producto a obtener
        empresa = body['empresa']  # Obtenemos la empresa desde el body

        # Obtener el producto de la tabla Products
        response = table.get_item(
            Key={'empresa': empresa, 'id_producto': id_producto}  # Usamos empresa como Partition Key y id_producto como Sort Key
        )

        product = response.get('Item', None)

        if not product:
            return {
                'statusCode': 404,
                'body': json.dumps({'message': 'Producto no encontrado'})
            }

        return {
            'statusCode': 200,
            'body': json.dumps({'product': product})
        }

    except Exception as e:
        return {'statusCode': 400, 'body': json.dumps({'error': str(e)})}
