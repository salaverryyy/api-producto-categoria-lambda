import json, os, urllib.request, urllib.error, boto3
from boto3.dynamodb.conditions import Key

# ─── Recursos ────────────────────────────────────────────────────────
dynamodb = boto3.resource("dynamodb")
table    = dynamodb.Table(os.environ["CATEGORIES_TABLE"])

VERIFY_TOKEN_URL: str = os.environ["VERIFY_TOKEN_URL"]    # https://…/usuarios/verify


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
        body          = json.loads(event.get("body") or "{}")
        tenant_id     = body.get("tenant_id")          # PK
        id_categoria  = body.get("id_categoria")
        id_producto   = body.get("id_producto")        # parte de la SK

        if not all([tenant_id, id_categoria, id_producto]):
            return {"statusCode": 400,
                    "body": json.dumps({
                        "message": "tenant_id, id_categoria e id_producto son requeridos"
                    })}

        id_cat_prod = f"{id_categoria}#{id_producto}"  # SK

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

        # ── 3) Actualización DynamoDB ───────────────────────────────
        resp = table.update_item(
            Key={
                "tenant_id": tenant_id,
                "id_categoria_producto": id_cat_prod
            },
            UpdateExpression="SET " + ", ".join(expr_parts),
            ExpressionAttributeValues=expr_vals,
            ReturnValues="ALL_NEW"
        )

        return {"statusCode": 200,
                "body": json.dumps({
                    "message": "Categoría actualizada",
                    "category": resp.get("Attributes", {})
                })}

    except Exception as e:
        return {"statusCode": 500,
                "body": json.dumps({"error": str(e)})}
