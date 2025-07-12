import json, uuid, boto3, os
from datetime import datetime

dynamodb   = boto3.resource('dynamodb')
table_name = os.getenv('PRODUCTS_TABLE')
table      = dynamodb.Table(table_name)

VERIFY_TOKEN_LAMBDA = os.getenv('VERIFY_TOKEN_LAMBDA')

def lambda_handler(event, context):
    try:
        # ---------- 1. Autenticación ----------
        auth = (event.get("headers") or {}).get("Authorization")
        if not auth:
            return {"statusCode": 401,
                    "body": json.dumps({"message": "Token no proporcionado"})}

        token = auth.split(" ")[1]
        lambda_client = boto3.client("lambda")
        auth_resp = lambda_client.invoke(
            FunctionName   = VERIFY_TOKEN_LAMBDA,
            InvocationType = "RequestResponse",
            Payload        = json.dumps({"token": token})
        )
        if json.loads(auth_resp["Payload"].read())["statusCode"] != 200:
            return {"statusCode": 403,
                    "body": json.dumps({"message": "Acceso no autorizado"})}

        # ---------- 2. Datos de entrada ----------
        body       = json.loads(event["body"])
        tenant_id  = body.get("empresa")          # Partition Key
        if not tenant_id:
            return {"statusCode": 400,
                    "body": json.dumps({"message": "empresa (tenant_id) requerido"})}

        id_producto    = str(uuid.uuid4())        # Sort Key
        fecha_creacion = datetime.utcnow().isoformat()

        # ---------- 3. Construir y guardar ítem ----------
        item = {
            "tenant_id"     : tenant_id,
            "id_producto"   : id_producto,
            "nombre"        : body["nombre"],
            "direccion"     : body["direccion"],
            "precio"        : body["precio"],
            "stock"         : body["stock"],
            "imagen_url"    : body.get("imagen_url", []),
            "fecha_creacion": fecha_creacion,
            "proveedor"     : body["proveedor"]
        }

        table.put_item(Item=item)

        # ---------- 4. Respuesta ----------
        return {"statusCode": 201, "body": json.dumps(item)}

    except Exception as e:
        return {"statusCode": 400,
                "body": json.dumps({"error": str(e)})}
