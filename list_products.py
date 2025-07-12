import json, os, boto3
from boto3.dynamodb.conditions import Key

# ─── DynamoDB ─────────────────────────────────────────────────────
dynamodb = boto3.resource("dynamodb")
table    = dynamodb.Table(os.environ["PRODUCTS_TABLE"])    # exige que exista

def lambda_handler(event, context):
    try:
        # 1) Leer parámetros de la query string ---------------------
        qs         = event.get("queryStringParameters") or {}
        tenant_id  = qs.get("tenant_id")     # ← clave de partición

        if not tenant_id:
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "message": "Debes enviar tenant_id en la query string"
                })
            }

        # 2) Consulta a DynamoDB -----------------------------------
        resp       = table.query(
            KeyConditionExpression=Key("tenant_id").eq(tenant_id)
        )
        productos  = resp.get("Items", [])

        # 3) Respuesta ---------------------------------------------
        return {"statusCode": 200,
                "body": json.dumps({"productos": productos})}

    except Exception as e:
        return {"statusCode": 500,
                "body": json.dumps({"error": str(e)})}
