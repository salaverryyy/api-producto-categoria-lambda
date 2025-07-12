import json, boto3, os

dynamodb   = boto3.resource("dynamodb")
table      = dynamodb.Table(os.getenv("CATEGORIES_TABLE"))
VERIFY_TOKEN_LAMBDA = os.getenv("VERIFY_TOKEN_LAMBDA")

def lambda_handler(event, context):
    try:
        # ---------- 1) Autenticación ----------
        auth = event["headers"].get("Authorization")
        if not auth:
            return {"statusCode": 401,
                    "body": json.dumps({"message": "Token no proporcionado"})}

        token = auth.split()[1]
        resp  = boto3.client("lambda").invoke(
            FunctionName   = VERIFY_TOKEN_LAMBDA,
            InvocationType = "RequestResponse",
            Payload        = json.dumps({"token": token})
        )
        if json.loads(resp["Payload"].read())["statusCode"] != 200:
            return {"statusCode": 403,
                    "body": json.dumps({"message": "Acceso no autorizado"})}

        # ---------- 2) Datos de entrada ----------
        body         = json.loads(event["body"])
        tenant_id    = body["empresa"]          # Partition Key
        id_categoria = body["id_categoria"]
        id_producto  = body["id_producto"]
        id_cat_prod  = f"{id_categoria}#{id_producto}"   # Sort Key

        # ---------- 3) Eliminación ----------
        table.delete_item(
            Key = {"tenant_id": tenant_id,
                   "id_categoria_producto": id_cat_prod},
            ConditionExpression = "attribute_exists(id_categoria_producto)"
        )

        return {"statusCode": 200,
                "body": json.dumps({"message": "Categoría eliminada correctamente"})}

    except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
        return {"statusCode": 404,
                "body": json.dumps({"message": "Categoría no encontrada"})}

    except Exception as e:
        return {"statusCode": 400,
                "body": json.dumps({"error": str(e)})}
