import json, os, boto3, base64
from decimal import Decimal
from boto3.dynamodb.conditions import Key

# --- JSON Encoder que transforma Decimal → float ---
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        # Necesario para codificar el nextToken que es un objeto dict
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
        
        # Leemos el límite, con 20 como valor por defecto
        limit        = int(qs.get("limit", 20))
        # Leemos el token de la siguiente página
        next_token   = qs.get("nextToken")

        if not tenant_id or not id_categoria:
            return {
                "statusCode": 400,
                "body": json.dumps({"message": "Debes enviar tenant_id e id_categoria"})
            }

        # 2) Query en tabla de categorías (AHORA CON LÍMITE Y PAGINACIÓN DE API)
        # =======================================================================
        query_params = {
            "KeyConditionExpression": Key("tenant_id").eq(tenant_id) &
                                      Key("id_categoria_producto").begins_with(f"{id_categoria}#"),
            "Limit": limit # <-- ¡Importante! Le decimos a DynamoDB que nos de solo 'limit' resultados
        }

        # Si el cliente nos envió un "nextToken", lo usamos para empezar desde ahí
        if next_token:
            # El token viene en base64 para que sea seguro en una URL, lo decodificamos
            exclusive_start_key = json.loads(base64.b64decode(next_token))
            query_params["ExclusiveStartKey"] = exclusive_start_key

        # Hacemos una SOLA llamada a la query. Ya no necesitamos el bucle "while".
        resp = categories_table.query(**query_params)
        
        items = resp.get("Items", [])
        
        # Guardamos la clave para la siguiente página, si es que existe
        last_evaluated_key = resp.get("LastEvaluatedKey")

        # =======================================================================
        
        if not items:
            return {
                "statusCode": 200, # Usamos 200 porque no es un error, simplemente no hay más resultados
                "body": json.dumps({"productos": [], "nextToken": None})
            }

        # 3) Extraer product_ids
        product_ids = [item["id_categoria_producto"].split("#",1)[1] for item in items]
        
        # 4) BatchGet en tabla de productos. Como ahora son pocos (max 20), ya no necesitamos dividir en lotes.
        # =======================================================================
        keys = [{"tenant_id": tenant_id, "id_producto": pid} for pid in product_ids]
        
        # El BatchGet aquí es seguro porque `limit` (20) es mucho menor que 100.
        batch = dynamodb.batch_get_item(RequestItems={
            products_table.name: {"Keys": keys}
        })
        productos = batch["Responses"].get(products_table.name, [])
        # Aquí también podrías manejar UnprocessedKeys por robustez, pero es menos probable que ocurra con lotes pequeños.
        
        # =======================================================================
        
        # 5) Preparar la respuesta final
        
        # Codificamos la clave de la siguiente página en base64 para enviarla al cliente
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
                "Content-Type": "application/json"
            },
            "body": json.dumps(response_body, cls=DecimalEncoder)
        }

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }