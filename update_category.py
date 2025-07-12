import json, boto3, os
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource("dynamodb")
table    = dynamodb.Table(os.getenv("CATEGORIES_TABLE"))
VERIFY_TOKEN_LAMBDA = os.getenv("VERIFY_TOKEN_LAMBDA")

def lambda_handler(event, context):
    try:
        # -------- 1) Autenticación --------
        auth = (event.get("headers") or {}).get("Authorization")
        if not auth:
            return {"statusCode": 401,
                    "body": json.dumps({"message": "Token no proporcionado"})}

        token = auth.split()[1]
        auth_resp = boto3.client("lambda").invoke(
            FunctionName   = VERIFY_TOKEN_LAMBDA,
            InvocationType = "RequestResponse",
            Payload        = json.dumps({"token": token})
        )
        if json.loads(auth_resp["Payload"].read().decode("utf-8"))["statusCode"] != 200:
            return {"statusCode": 403,
                    "body": json.dumps({"message": "Acceso no autorizado"})}

        # -------- 2) Datos de entrada -----
        body = json.loads(event.get("body") or "{}")

        tenant_id    = body.get("empresa")          # PK
        id_categoria = body.get("id_categoria")
        id_producto  = body.get("id_producto")      # necesario para la SK

        if not (tenant_id and id_categoria and id_producto):
            return {"statusCode": 400,
                    "body": json.dumps(
                        {"message": "empresa, id_categoria e id_producto son requeridos"}
                    )}

        id_cat_prod = f"{id_categoria}#{id_producto}"   # SK

        # Campos permitidos a actualizar
        update_fields = ["nombre", "descripcion"]
        expr_parts, expr_vals = [], {}

        for f in update_fields:
            if f in body:
                expr_parts.append(f"{f} = :{f}")
                expr_vals[f":{f}"] = body[f]

        if not expr_parts:
            return {"statusCode": 400,
                    "body": json.dumps({"message": "No hay campos para actualizar"})}

        # -------- 3) Actualización ----------
        resp = table.update_item(
            Key={
                "tenant_id"            : tenant_id,
                "id_categoria_producto": id_cat_prod
            },
            UpdateExpression      = "SET " + ", ".join(expr_parts),
            ExpressionAttributeValues = expr_vals,
            ReturnValues          = "ALL_NEW"
        )

        return {"statusCode": 200,
                "body": json.dumps(
                    {"message": "Categoría actualizada",
                     "category": resp.get("Attributes", {})}
                )}

    except Exception as e:
        return {"statusCode": 400,
                "body": json.dumps({"error": str(e)})}
