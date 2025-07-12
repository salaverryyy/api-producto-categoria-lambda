import json, os, urllib.request, urllib.error, boto3

# ─── DynamoDB ─────────────────────────────────────────────────
dynamodb = boto3.resource("dynamodb")
table    = dynamodb.Table(os.environ["CATEGORIES_TABLE"])   # falla temprano si falta

# ─── URL del verificador de JWT ──────────────────────────────
VERIFY_TOKEN_URL: str = os.environ["VERIFY_TOKEN_URL"] 


def _verify_token(token: str) -> bool:
    """Devuelve True si VERIFY_TOKEN_URL responde 200."""
    req = urllib.request.Request(VERIFY_TOKEN_URL, method="GET")
    req.add_header("Authorization", f"Bearer {token}")

    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status == 200
    except urllib.error.HTTPError:
        return False          # 4xx/5xx ⇒ token inválido
    except Exception:
        return False          # timeout, DNS, etc.


def lambda_handler(event, context):
    try:
        # ─── 1) Autenticación ───────────────────────────────
        auth = (event.get("headers") or {}).get("Authorization")
        if not auth:
            return {"statusCode": 401,
                    "body": json.dumps({"message": "Token no proporcionado"})}

        token = auth.split()[1]
        if not _verify_token(token):
            return {"statusCode": 403,
                    "body": json.dumps({"message": "Acceso no autorizado"})}

        # ─── 2) Datos de entrada ────────────────────────────
        body          = json.loads(event.get("body") or "{}")
        tenant_id     = body.get("tenant_id")           # PK
        id_categoria  = body.get("id_categoria")
        id_producto   = body.get("id_producto")

        if not all([tenant_id, id_categoria, id_producto]):
            return {"statusCode": 400,
                    "body": json.dumps({"message": "Faltan campos obligatorios"})}

        id_cat_prod = f"{id_categoria}#{id_producto}"   # SK

        # ─── 3) Eliminación en DynamoDB ─────────────────────
        table.delete_item(
            Key={
                "tenant_id": tenant_id,
                "id_categoria_producto": id_cat_prod
            },
            ConditionExpression="attribute_exists(id_categoria_producto)"
        )

        return {"statusCode": 200,
                "body": json.dumps({"message": "Categoría eliminada correctamente"})}

    except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
        return {"statusCode": 404,
                "body": json.dumps({"message": "Categoría no encontrada"})}

    except Exception as e:
        return {"statusCode": 500,
                "body": json.dumps({"error": str(e)})}
