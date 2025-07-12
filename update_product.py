import json, os, urllib.request, urllib.error, boto3

# ─── DynamoDB ─────────────────────────────────────────────────────
dynamodb = boto3.resource("dynamodb")
table    = dynamodb.Table(os.environ["PRODUCTS_TABLE"])       # falla temprano si falta

VERIFY_TOKEN_URL: str = os.environ["VERIFY_TOKEN_URL"]        # https://…/usuarios/verify


def _verify_token(token: str) -> bool:
    """Devuelve True si VERIFY_TOKEN_URL responde 200."""
    req = urllib.request.Request(VERIFY_TOKEN_URL, method="GET")
    req.add_header("Authorization", f"Bearer {token}")

    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status == 200
    except urllib.error.HTTPError:
        return False
    except Exception:
        return False


def lambda_handler(event, context):
    try:
        # ── 1) Autenticación ───────────────────────────────────────
        auth = (event.get("headers") or {}).get("Authorization")
        if not auth:
            return {"statusCode": 401,
                    "body": json.dumps({"message": "Token no proporcionado"})}

        token = auth.split()[1]
        if not _verify_token(token):
            return {"statusCode": 403,
                    "body": json.dumps({"message": "Acceso no autorizado"})}

        # ── 2) Datos de entrada ────────────────────────────────────
        body        = json.loads(event.get("body") or "{}")
        tenant_id   = body.get("tenant_id")        # ← PK
        id_producto = body.get("id_producto")      # ← SK

        if not tenant_id or not id_producto:
            return {"statusCode": 400,
                    "body": json.dumps({
                        "message": "tenant_id e id_producto son requeridos"
                    })}

        # ── 3) Construir expresión de actualización ───────────────
        mutable_fields = [
            "nombre", "direccion", "precio", "stock",
            "imagen_url", "proveedor"
        ]
        expr_parts, expr_vals = [], {}

        for f in mutable_fields:
            if f in body:
                expr_parts.append(f"{f} = :{f}")
                expr_vals[f":{f}"] = (
                    json.dumps(body[f]) if f == "imagen_url" else body[f]
                )

        if not expr_parts:
            return {"statusCode": 400,
                    "body": json.dumps({"message": "No hay campos para actualizar"})}

        # ── 4) Llamada UpdateItem ─────────────────────────────────
        resp = table.update_item(
            Key={
                "tenant_id": tenant_id,
                "id_producto": id_producto
            },
            UpdateExpression="SET " + ", ".join(expr_parts),
            ExpressionAttributeValues=expr_vals,
            ReturnValues="ALL_NEW"
        )

        return {"statusCode": 200,
                "body": json.dumps({
                    "message": "Producto actualizado",
                    "product": resp.get("Attributes", {})
                })}

    except Exception as e:
        return {"statusCode": 500,
                "body": json.dumps({"error": str(e)})}
