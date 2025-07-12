import json, uuid, os, urllib.request, urllib.error, boto3

# ─── DynamoDB ──────────────────────────────────────────────────
dynamodb = boto3.resource("dynamodb")
table    = dynamodb.Table(os.getenv("CATEGORIES_TABLE"))

# URL del verificador de token (API Gateway)
VERIFY_TOKEN_URL = os.getenv("VERIFY_TOKEN_URL")


def _verify_token(token: str) -> bool:
    """
    Devuelve True si VERIFY_TOKEN_URL responde 200.
    """
    req = urllib.request.Request(VERIFY_TOKEN_URL, method="GET")
    req.add_header("Authorization", f"Bearer {token}")

    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status == 200
    except urllib.error.HTTPError:
        return False    # 4xx/5xx ⇒ token inválido
    except Exception:
        return False    # timeout, DNS, etc.


def lambda_handler(event, context):
    try:
        # ─── 1) Autenticación ──────────────────────────────
        headers = event.get("headers") or {}
        auth    = headers.get("Authorization")
        if not auth:
            return {"statusCode": 401,
                    "body": json.dumps({"message": "Token no proporcionado"})}

        token = auth.split()[1]
        if not _verify_token(token):
            return {"statusCode": 403,
                    "body": json.dumps({"message": "Acceso no autorizado"})}

        # ─── 2) Datos de entrada ───────────────────────────
        body          = json.loads(event.get("body") or "{}")
        tenant_id     = body.get("tenant_id")
        id_producto   = body.get("id_producto")
        nombre    = body.get("nombre")

        if not all([tenant_id, id_producto, nombre]):
            return {"statusCode": 400,
                    "body": json.dumps({"message": "Faltan campos obligatorios"})}

        id_categoria          = str(uuid.uuid4())
        id_categoria_producto = f"{id_categoria}#{id_producto}"

        item = {
            "tenant_id": tenant_id,                   # PK
            "id_categoria_producto": id_categoria_producto,  # SK
            "nombre": nombre,
            "descripcion": body.get("descripcion", "")
        }

        # ─── 3) Insertar en DynamoDB ──────────────────────
        table.put_item(Item=item)

        return {"statusCode": 201, "body": json.dumps(item)}

    except Exception as e:
        return {"statusCode": 500,
                "body": json.dumps({"error": str(e)})}
