import json
from decimal import Decimal
import os, boto3
from boto3.dynamodb.conditions import Key

# ─── JSON Encoder que transforma Decimal → float ───────────────
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)

# ─── DynamoDB ─────────────────────────────────────────────────────
dynamodb = boto3.resource("dynamodb")
table    = dynamodb.Table(os.environ["PRODUCTS_TABLE"])

def lambda_handler(event, context):
    try:
        # 1) Leer parámetros de la query string ---------------------
        qs        = event.get("queryStringParameters") or {}
        tenant_id = qs.get("tenant_id")

        if not tenant_id:
            return {
                "statusCode": 400,
                "body": json.dumps(
                    {"message": "Debes enviar tenant_id en la query string"}
                )
            }

        # 2) Consulta a DynamoDB -----------------------------------
        resp      = table.query(
            KeyConditionExpression=Key("tenant_id").eq(tenant_id)
        )
        productos = resp.get("Items", [])

        # 3) Respuesta con encoder para Decimal -------------------
        return {
            "statusCode": 200,
            "body": json.dumps({"productos": productos}, cls=DecimalEncoder)
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
