import json
import uuid
import boto3
import os
from datetime import datetime

# Crear un cliente DynamoDB
dynamodb = boto3.resource('dynamodb')
table_name = os.getenv('CATEGORIES_TABLE')  # Usamos la variable de entorno para el nombre de la tabla
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

        # Si el token es válido, continuar con la creación de la categoría
        body = json.loads(event['body'])

        # Generar un ID único para la categoría (puedes usar el UUID como en el caso de usuario)
        id_categoria = str(uuid.uuid4())  # Generamos un UUID para la categoría

        fecha_creacion = datetime.utcnow().isoformat()  # Fecha de creación en formato ISO 8601

        # Definir el item que se insertará en la tabla
        item = {
            'id_categoria': id_categoria,   # Usamos el UUID generado como id_categoria
            'nombre': body['nombre'],
            'descripcion': body['descripcion'],
            'fecha_creacion': fecha_creacion
        }

        # Insertar la nueva categoría en DynamoDB
        table.put_item(Item=item)

        # Devolver la respuesta con la categoría creada
        return {
            'statusCode': 201,
            'body': json.dumps({'id_categoria': id_categoria, 'nombre': body['nombre'], 'descripcion': body['descripcion'], 'fecha_creacion': fecha_creacion})
        }

    except Exception as e:
        # Si ocurre un error, devolver un error con el mensaje correspondiente
        return {
            'statusCode': 400,
            'body': json.dumps({'error': str(e)})
        }
