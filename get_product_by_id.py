import json, os, boto3

# ─── DynamoDB ───────────────────────────────────────────────────────
dynamodb = boto3.resource("dynamodb")
table    = dynamodb.Table(os.environ["PRODUCTS_TABLE"])   # obliga a que exista

def lambda_handler(event, context):
    try:
        # ── 1) Leer parámetros de la query - GET ─────────────────────
        qs          = event.get("queryStringParameters") or {}
        tenant_id   = qs.get("tenant_id")
        id_producto = qs.get("id_producto")

        if not tenant_id or not id_producto:
            return {"statusCode": 400,
                    "body": json.dumps({
                        "message": "Debes enviar tenant_id e id_producto en la query string"
                    })}

        # ── 2) Buscar en DynamoDB ───────────────────────────────────
        resp = table.get_item(
            Key={
                "tenant_id": tenant_id,
                "id_producto": id_producto
            }
        )
        item = resp.get("Item")
        if not item:
            return {"statusCode": 404,
                    "body": json.dumps({"message": "Producto no encontrado"})}

        # ── 3) Respuesta OK ─────────────────────────────────────────
        return {"statusCode": 200,
                "body": json.dumps({"product": item})}

    except Exception as e:
        return {"statusCode": 500,
                "body": json.dumps({"error": str(e)})}
