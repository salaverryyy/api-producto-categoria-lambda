import json, os, boto3
from boto3.dynamodb.conditions import Key

# ─── DynamoDB ─────────────────────────────────────────────────────
dynamodb = boto3.resource("dynamodb")
table    = dynamodb.Table(os.environ["CATEGORIES_TABLE"])   # exige que exista

def lambda_handler(event, context):
    try:
        # 1) Leer parámetros de la query string ---------------------
        qs         = event.get("queryStringParameters") or {}
        tenant_id  = qs.get("tenant_id")          # PK

        if not tenant_id:
            return {
                "statusCode": 400,
                "headers": { # <--- Añade los encabezados CORS aquí
                    "Access-Control-Allow-Origin": "*", # Permite cualquier origen (para desarrollo)
                    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                    "Access-Control-Allow-Methods": "GET,OPTIONS" # Ajusta los métodos según lo que uses
                },
                "body": json.dumps({
                    "message": "Debes enviar tenant_id en la query string"
                })
            }

        # 2) Consulta por todas las categorías del tenant ----------
        response   = table.query(
            KeyConditionExpression=Key("tenant_id").eq(tenant_id)
        )
        categorias = response.get("Items", [])

        # 2.1) Filtrar categorías únicas por nombre y contar entradas
        categorias_unicas = {}
        for cat in categorias:
            nombre = cat["nombre"]
            if nombre not in categorias_unicas:
                categorias_unicas[nombre] = {
                    **cat,
                    "cantidad_entradas": 1
                }
            else:
                categorias_unicas[nombre]["cantidad_entradas"] += 1
        categorias_unicas_list = list(categorias_unicas.values())

        # 3) Respuesta ---------------------------------------------
        return {
            "statusCode": 200,
            "headers": { # <--- Añade los encabezados CORS aquí
                "Access-Control-Allow-Origin": "*", # Permite cualquier origen (para desarrollo)
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "GET,OPTIONS" # Ajusta los métodos según lo que uses
            },
            "body": json.dumps({"categorias": categorias_unicas_list})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": { # <--- Y también en caso de error
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "GET,OPTIONS"
            },
            "body": json.dumps({"error": str(e)})
        }