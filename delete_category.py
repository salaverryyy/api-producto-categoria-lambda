import json
import boto3
import os

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

        # Si el token es válido, continuar con la eliminación de la categoría
        body = json.loads(event['body'])
        id_categoria = body['id_categoria']  # ID de la categoría a eliminar
        empresa = body['empresa']  # Obtenemos la empresa desde el body

        # Eliminar la categoría de la tabla
        response = table.delete_item(
            Key={'empresa': empresa, 'id_categoria': id_categoria},  # Usamos empresa como Partition Key y id_categoria como Sort Key
            ConditionExpression='attribute_exists(id_categoria)'  # Evitar eliminar un registro inexistente
        )

        # Devolver una respuesta de éxito
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Categoría eliminada correctamente'})
        }

    except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
        # Si no existe la categoría, devolver error 404
        return {
            'statusCode': 404,
            'body': json.dumps({'message': 'Categoría no encontrada'})
        }

    except Exception as e:
        # Si ocurre otro error, devolver el error correspondiente
        return {
            'statusCode': 400,
            'body': json.dumps({'error': str(e)})
        }
