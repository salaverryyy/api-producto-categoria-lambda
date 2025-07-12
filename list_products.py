import json, boto3, os
from boto3.dynamodb.conditions import Key   # ← para construir la query

dynamodb = boto3.resource("dynamodb")
table    = dynamodb.Table(os.getenv("PRODUCTS_TABLE"))
VERIFY_TOKEN_LAMBDA = os.getenv("VERIFY_TOKEN_LAMBDA")

def lambda_handler(event, context):
    try:
        # ---------- 1) Autenticación ----------
        headers = event.get("headers") or {}
        auth = headers.get("Authorization")
        if not auth:
            return {
                "statusCode": 401,
                "body": json.dumps({"message": "Token no proporcionado"})
            }

        token = auth.split()[1]
        resp  = boto3.client("lambda").invoke(
            FunctionName   = VERIFY_TOKEN_LAMBDA,
            InvocationType = "RequestResponse",
            Payload        = json.dumps({"token": token})
        )
        if json.loads(resp["Payload"].read().decode("utf-8"))["statusCode"] != 200:
            return {
                "statusCode": 403,
                "body": json.dumps({"message": "Acceso no autorizado"})
            }

        # ---------- 2) Datos de entrada ----------
        body       = json.loads(event.get("body") or "{}")
        tenant_id  = body.get("empresa")                # misma clave que envía el front
        if not tenant_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"message": "Empresa (tenant_id) no proporcionada"})
            }

        # ---------- 3) Consulta a DynamoDB ----------
        response = table.query(
            KeyConditionExpression = Key("tenant_id").eq(tenant_id)
        )
        productos = response.get("Items", [])

        return {
            "statusCode": 200,
            "body": json.dumps({"productos": productos})
        }

    except Exception as e:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": str(e)})
        }
