import json, os, boto3
from boto3.dynamodb.conditions import Key

dynamodb          = boto3.resource("dynamodb")
category_table    = dynamodb.Table(os.environ["PRODUCT_CATEGORY_TABLE"])
products_table    = dynamodb.Table(os.environ["PRODUCTS_TABLE"])

def lambda_handler(event, context):
    try:
        # ── 1) Leer parámetros de la query string ──────────────────
        qs          = event.get("queryStringParameters") or {}
        id_categoria = qs.get("id_categoria")

        if not id_categoria:
            return {"statusCode": 400,
                    "body": json.dumps({
                        "message": "Debes enviar id_categoria en la query string"
                    })}

        # ── 2) Obtener ids de productos para la categoría ──────────
        resp = category_table.query(
            KeyConditionExpression=Key("id_categoria").eq(id_categoria)
        )
        product_ids = [item["id_producto"] for item in resp.get("Items", [])]

        if not product_ids:
            return {"statusCode": 404,
                    "body": json.dumps({
                        "message": "No se encontraron productos para esta categoría"
                    })}

        # ── 3) BatchGet en la tabla Products ───────────────────────
        keys = [{"id_producto": pid} for pid in product_ids]
        batch_resp = dynamodb.batch_get_item(
            RequestItems={
                products_table.name: {
                    "Keys": keys
                }
            }
        )
        productos = batch_resp["Responses"].get(products_table.name, [])

        # ── 4) Respuesta OK ─────────────────────────────────────────
        return {"statusCode": 200,
                "body": json.dumps({"productos": productos})}

    except Exception as e:
        return {"statusCode": 500,
                "body": json.dumps({"error": str(e)})}
