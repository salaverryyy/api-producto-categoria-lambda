import json, os, boto3
from boto3.dynamodb.conditions import Key

dynamodb         = boto3.resource("dynamodb")
# Usamos la misma tabla de categorías como tabla puente
categories_table = dynamodb.Table(os.environ["CATEGORIES_TABLE"])
products_table   = dynamodb.Table(os.environ["PRODUCTS_TABLE"])

def lambda_handler(event, context):
    try:
        # 1) Leer query params
        qs           = event.get("queryStringParameters") or {}
        tenant_id    = qs.get("tenant_id")
        id_categoria = qs.get("id_categoria")

        if not tenant_id or not id_categoria:
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "message": "Debes enviar tenant_id e id_categoria en la query string"
                })
            }

        # 2) Query en tabla de categorías para ese tenant y categoría
        resp = categories_table.query(
            KeyConditionExpression=Key("tenant_id").eq(tenant_id) &
                                   Key("id_categoria_producto").begins_with(f"{id_categoria}#")
        )
        items = resp.get("Items", [])

        if not items:
            return {
                "statusCode": 404,
                "body": json.dumps({
                    "message": "No se encontraron productos para esta categoría"
                })
            }

        # 3) Extraer product_ids de la SK (<id_categoria>#<id_producto>)
        product_ids = [ item["id_categoria_producto"].split("#",1)[1] for item in items ]

        # 4) BatchGet en tabla de productos
        keys = [{ "tenant_id": tenant_id, "id_producto": pid } for pid in product_ids]
        batch = dynamodb.batch_get_item(
            RequestItems={
                products_table.name: {
                    "Keys": keys
                }
            }
        )
        productos = batch["Responses"].get(products_table.name, [])

        # 5) Responder
        return {
            "statusCode": 200,
            "body": json.dumps({"productos": productos})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
