import json, uuid, boto3, os
from datetime import datetime

dynamodb   = boto3.resource('dynamodb')
table_name = os.getenv('CATEGORIES_TABLE')
table      = dynamodb.Table(table_name)

VERIFY_TOKEN_LAMBDA = os.getenv('VERIFY_TOKEN_LAMBDA')

def lambda_handler(event, context):
    try:
        # --- Autenticación idéntica ---
        auth_header = event['headers'].get('Authorization')
        if not auth_header:
            return {'statusCode': 401, 'body': json.dumps({'message': 'Token no proporcionado'})}

        token = auth_header.split(" ")[1]
        lambda_client  = boto3.client('lambda')
        payload_string = json.dumps({'token': token})
        resp = lambda_client.invoke(
            FunctionName=VERIFY_TOKEN_LAMBDA,
            InvocationType='RequestResponse',
            Payload=payload_string
        )
        if json.loads(resp['Payload'].read())['statusCode'] != 200:
            return {'statusCode': 403, 'body': json.dumps({'message': 'Acceso no autorizado'})}

        # --- Datos de entrada ---
        body        = json.loads(event['body'])
        tenant_id   = body['empresa']           # <- nuevo nombre
        id_producto = body['id_producto']         # <- necesario para la SK
        id_categoria = str(uuid.uuid4())
        id_categoria_producto    = f"{id_categoria}#{id_producto}"  # <- Sort Key

        item = {
            'tenant_id': tenant_id,     # PK
            'id_categoria_producto' : id_categoria_producto,      # SK    
            'nombre'      : body['nombre'],
            'descripcion' : body['descripcion'],
        }

        table.put_item(Item=item)

        return {
            'statusCode': 201,
            'body': json.dumps(item)
        }

    except Exception as e:
        return {'statusCode': 400, 'body': json.dumps({'error': str(e)})}
