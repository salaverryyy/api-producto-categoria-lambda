import json, os, boto3, base64
from decimal import Decimal
from boto3.dynamodb.conditions import Key

# --- JSON Encoder que transforma Decimal → float ---
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        if isinstance(o, bytes):
            return o.decode('utf-8')
        return super().default(o)

# --- Recursos DynamoDB ---
dynamodb         = boto3.resource("dynamodb")
categories_table = dynamodb.Table(os.environ["CATEGORIES_TABLE"])
products_table   = dynamodb.Table(os.environ["PRODUCTS_TABLE"])

def lambda_handler(event, context):
    try:
        # 1) Leer query params, incluyendo los de paginación
        qs           = event.get("queryStringParameters") or {}
        tenant_id    = qs.get("tenant_id")
        id_categoria = qs.get("id_categoria")
        
        limit        = int(qs.get("limit", 20))
        next_token   = qs.get("nextToken")

        if not tenant_id or not id_categoria:
            return {
                "statusCode": 400,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                    "Access-Control-Allow-Methods": "GET,OPTIONS",
                    "Content-Type": "application/json"
                },
                "body": json.dumps({"message": "Debes enviar tenant_id e id_categoria"})
            }

        query_params = {
            "KeyConditionExpression": Key("tenant_id").eq(tenant_id) &
                                      Key("id_categoria_producto").begins_with(f"{id_categoria}#"),
            "Limit": limit
        }

        if next_token:
            exclusive_start_key = json.loads(base64.b64decode(next_token))
            query_params["ExclusiveStartKey"] = exclusive_start_key

        resp = categories_table.query(**query_params)
        items = resp.get("Items", [])
        last_evaluated_key = resp.get("LastEvaluatedKey")

        if not items:
            return {
                "statusCode": 200,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                    "Access-Control-Allow-Methods": "GET,OPTIONS",
                    "Content-Type": "application/json"
                },
                "body": json.dumps({"productos": [], "nextToken": None})
            }

        product_ids = [item["id_categoria_producto"].split("#",1)[1] for item in items]
        keys = [{"tenant_id": tenant_id, "id_producto": pid} for pid in product_ids]
        batch = dynamodb.batch_get_item(RequestItems={
            products_table.name: {"Keys": keys}
        })
        productos = batch["Responses"].get(products_table.name, [])

        new_next_token = None
        if last_evaluated_key:
            new_next_token = base64.b64encode(json.dumps(last_evaluated_key, cls=DecimalEncoder).encode('utf-8')).decode('utf-8')

        response_body = {
            "productos": productos,
            "nextToken": new_next_token
        }

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "GET,OPTIONS",
                "Content-Type": "application/json"
            },
            "body": json.dumps(response_body, cls=DecimalEncoder)
        }

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "GET,OPTIONS",
                "Content-Type": "application/json"
            },
            "body": json.dumps({"error": str(e)})
        }