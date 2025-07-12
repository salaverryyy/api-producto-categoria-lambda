import json, os, urllib.request, urllib.error, boto3

# ─── Configuración y recursos ──────────────────────────────────────────
dynamodb = boto3.resource("dynamodb")
table    = dynamodb.Table(os.environ["PRODUCTS_TABLE"])        # exige que exista

VERIFY_TOKEN_URL: str = os.environ["VERIFY_TOKEN_URL"]         # https://…/usuarios/verify


def _verify_token(token: str) -> bool:
    """ Devuelve True si VERIFY_TOKEN_URL responde 200. """
    req = urllib.request.Request(VERIFY_TOKEN_URL, method="GET")
    req.add_header("Authorization", f"Bearer {token}")

    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status == 200
    except urllib.error.HTTPError:
        return False           # 4xx/5xx ⇒ token inválido
    except Exception:
        return False           # timeout, DNS, etc.


def lambda_handler(event, context):
    try:
        # ── 1) Autenticación ───────────────────────────────────────────
        auth = (event.get("headers") or {}).get("Authorization")
        if not auth:
            return {"statusCode": 401,
                    "body": json.dumps({"message": "Token no proporcionado"})}

        token = auth.split()[1]
        if not _verify_token(token):
            return {"statusCode": 403,
                    "body": json.dumps({"message": "Acceso no autorizado"})}

        # ── 2) Datos de entrada ────────────────────────────────────────
        body        = json.loads(event.get("body") or "{}")
        tenant_id   = body.get("tenant_id")         # ← PK
        id_producto = body.get("id_producto")       # ← SK

        if not tenant_id or not id_producto:
            return {"statusCode": 400,
                    "body": json.dumps({"message": "Faltan tenant_id o id_producto"})}

        # ── 3) Eliminación en DynamoDB ─────────────────────────────────
        table.delete_item(
            Key={
                "tenant_id": tenant_id,
                "id_producto": id_producto
            },
            ConditionExpression="attribute_exists(id_producto)"
        )

        return {"statusCode": 200,
                "body": json.dumps({"message": "Producto eliminado correctamente"})}

    except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
        return {"statusCode": 404,
                "body": json.dumps({"message": "Producto no encontrado"})}

    except Exception as e:
        return {"statusCode": 500,
                "body": json.dumps({"error": str(e)})}
