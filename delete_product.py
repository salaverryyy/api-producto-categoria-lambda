import json, boto3, os

dynamodb = boto3.resource("dynamodb")
table    = dynamodb.Table(os.getenv("PRODUCTS_TABLE"))
VERIFY_TOKEN_LAMBDA = os.getenv("VERIFY_TOKEN_LAMBDA")

def lambda_handler(event, context):
    try:
        # --- Autenticación -------------
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
        if json.loads(resp["Payload"].read().decode("utf-8"))["statusCode"] != 200:
            return {"statusCode": 403,
                "body": json.dumps({"message": "Acceso no autorizado"})}


        # --- Datos de entrada ----------
        body        = json.loads(event["body"])
        tenant_id   = body["empresa"]       # ahora es nuestro PK
        id_producto = body["id_producto"]

        # --- Eliminación ---------------
        table.delete_item(
            Key={"tenant_id": tenant_id, "id_producto": id_producto},
            ConditionExpression="attribute_exists(id_producto)"
        )

        return {"statusCode": 200,
                "body": json.dumps({"message": "Producto eliminado correctamente"})}

    except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
        return {"statusCode": 404,
                "body": json.dumps({"message": "Producto no encontrado"})}

    except Exception as e:
        return {"statusCode": 400,
                "body": json.dumps({"error": str(e)})}
