import json, boto3, os, uuid
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource("dynamodb")
table    = dynamodb.Table(os.getenv("PRODUCTS_TABLE"))
VERIFY_TOKEN_LAMBDA = os.getenv("VERIFY_TOKEN_LAMBDA")

def lambda_handler(event, context):
    try:
        # ---------- 1) Autenticación ----------
        auth = (event.get("headers") or {}).get("Authorization")
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

        # ---------- 2) Datos de entrada ----------
        body        = json.loads(event.get("body") or "{}")
        tenant_id   = body.get("empresa")          # ahora PK = tenant_id
        id_producto = body.get("id_producto")

        if not (tenant_id and id_producto):
            return {"statusCode": 400,
                    "body": json.dumps({"message": "empresa y id_producto son requeridos"})}

        # ---------- 3) Campos a actualizar -------
        mutable = ["nombre", "direccion", "precio", "stock",
                   "imagen_url", "proveedor"]
        expr_parts, expr_vals = [], {}

        for f in mutable:
            if f in body:
                expr_parts.append(f"{f} = :{f}")
                expr_vals[f":{f}"] = (json.dumps(body[f])
                                      if f == "imagen_url" else body[f])

        if not expr_parts:
            return {"statusCode": 400,
                    "body": json.dumps({"message": "No hay campos para actualizar"})}

        # ---------- 4) UpdateItem ----------------
        resp = table.update_item(
            Key={
                "tenant_id"  : empresa,   # PK
                "id_producto": id_producto  # SK
            },
            UpdateExpression      = "SET " + ", ".join(expr_parts),
            ExpressionAttributeValues = expr_vals,
            ReturnValues          = "ALL_NEW"
        )

        return {"statusCode": 200,
                "body": json.dumps(
                    {"message": "Producto actualizado",
                     "product": resp.get("Attributes", {})}
                )}

    except Exception as e:
        return {"statusCode": 400,
                "body": json.dumps({"error": str(e)})}
