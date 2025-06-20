import os
import boto3

# Crear un cliente de DynamoDB usando las credenciales de AWS automáticamente gestionadas por Serverless
dynamodb = boto3.resource('dynamodb')

# Obtener los nombres de las tablas desde las variables de entorno configuradas en serverless.yml
PRODUCTS_TABLE   = os.environ.get('PRODUCTS_TABLE', 'ProductsDev')
CATEGORIES_TABLE = os.environ.get('CATEGORIES_TABLE', 'CategoriesDev')

# Obtener las referencias a las tablas de DynamoDB
products_table   = dynamodb.Table(PRODUCTS_TABLE)
categories_table = dynamodb.Table(CATEGORIES_TABLE)
