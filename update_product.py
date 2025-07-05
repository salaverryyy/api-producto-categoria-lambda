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

        # Si el token es válido, continuar con la actualización del producto
        body = json.loads(event['body'])
        id_producto = body['id_producto']  # ID del producto a actualizar

        # Campos que se pueden actualizar
        update_fields = ['nombre', 'direccion', 'precio', 'stock', 'imagen_url', 'proveedor', 'category']

        # Construir expresión de actualización dinámica
        update_expression = []
        expression_values = {}

        for field in update_fields:
            if field in body:
                update_expression.append(f"{field} = :{field}")
                expression_values[f":{field}"] = body[field] if field != 'imagen_url' else json.dumps(body[field])

        if not update_expression:
            return {'statusCode': 400, 'body': json.dumps({'message': 'No hay campos para actualizar'})}

        # Realizar la actualización en DynamoDB
        response = table.update_item(
            Key={'id_producto': id_producto},
            UpdateExpression="SET " + ", ".join(update_expression),
            ExpressionAttributeValues=expression_values,
            ReturnValues="ALL_NEW"
        )

        updated_product = response.get('Attributes', {})

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Producto actualizado', 'product': updated_product})
        }

    except Exception as e:
        return {'statusCode': 400, 'body': json.dumps({'error': str(e)})}
