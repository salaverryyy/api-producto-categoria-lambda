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
                "body": json.dumps({
                    "message": "Debes enviar tenant_id en la query string"
                })
            }

        # 2) Consulta por todas las categorías del tenant ----------
        response   = table.query(
            KeyConditionExpression=Key("tenant_id").eq(tenant_id)
        )
        categorias = response.get("Items", [])

        # 2.1) Filtrar categorías únicas por nombre
        categorias_unicas = {}
        for cat in categorias:
            nombre = cat["nombre"]
            # Solo guardar la primera ocurrencia de cada nombre
            if nombre not in categorias_unicas:
                categorias_unicas[nombre] = cat
        categorias_unicas_list = list(categorias_unicas.values())

        # 3) Respuesta ---------------------------------------------
        return {"statusCode": 200,
                "body": json.dumps({"categorias": categorias_unicas_list})}

    except Exception as e:
        return {"statusCode": 500,
                "body": json.dumps({"error": str(e)})}