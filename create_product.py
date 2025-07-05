import json
import uuid
import boto3
import os
from datetime import datetime

# Crear un cliente DynamoDB
dynamodb = boto3.resource('dynamodb')
table_name = os.getenv('PRODUCTS_TABLE')  # Usamos la variable de entorno para el nombre de la tabla
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

        # Si el token es válido, continuar con la creación del producto
        body = json.loads(event['body'])

        # Generar un ID único para el producto
        id_producto = str(uuid.uuid4())  # Generamos un UUID para el producto

        # Obtener la empresa desde el body
        empresa = body.get('empresa')  # Ahora tomamos la empresa desde el body

        fecha_creacion = datetime.utcnow().isoformat()  # Fecha de creación en formato ISO 8601

        # Definir el item que se insertará en la tabla
        item = {
            'empresa': empresa,  # Partition Key
            'id_producto': id_producto,   # Sort Key
            'nombre': body['nombre'],
            'direccion': body['direccion'],
            'precio': body['precio'],
            'stock': body['stock'],
            'imagen_url': body.get('imagen_url', []),  # Permitir lista vacía si no hay imágenes
            'fecha_creacion': fecha_creacion,
            'proveedor': body['proveedor'],
            'category': body['category']  # La categoría se asume como un string
        }

        # Insertar el nuevo producto en DynamoDB
        table.put_item(Item=item)

        # Devolver la respuesta con el producto creado
        return {
            'statusCode': 201,
            'body': json.dumps({
                'empresa': empresa,
                'id_producto': id_producto,
                'nombre': body['nombre'],
                'direccion': body['direccion'],
                'precio': body['precio'],
                'stock': body['stock'],
                'imagen_url': body.get('imagen_url', []),
                'fecha_creacion': fecha_creacion,
                'proveedor': body['proveedor'],
                'category': body['category']
            })
        }

    except Exception as e:
        # Si ocurre un error, devolver un error con el mensaje correspondiente
        return {
            'statusCode': 400,
            'body': json.dumps({'error': str(e)})
        }
