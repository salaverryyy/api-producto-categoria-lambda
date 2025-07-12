import json, uuid, os, urllib.request, urllib.error, boto3
from datetime import datetime
from typing import cast

# ─── Recursos AWS ─────────────────────────────────────────────
dynamodb = boto3.resource("dynamodb")
table    = dynamodb.Table(os.environ["PRODUCTS_TABLE"])   # falla rápido si falta

VERIFY_TOKEN_URL: str = os.environ["VERIFY_TOKEN_URL"]    # endpoint HTTPS


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
        return False      # 4xx/5xx ⇒ token inválido
    except Exception:
        return False      # timeout, DNS, etc.


def lambda_handler(event, context):
    try:
        # ── 1) Autenticación ─────────────────────────────────
        auth = (event.get("headers") or {}).get("Authorization")
        if not auth:
            return {"statusCode": 401,
                    "body": json.dumps({"message": "Token no proporcionado"})}

        token = auth.split()[1]
        if not _verify_token(token):
            return {"statusCode": 403,
                    "body": json.dumps({"message": "Acceso no autorizado"})}

        # ── 2) Datos de entrada ──────────────────────────────
        body = json.loads(event.get("body") or "{}")
        tenant_id = body.get("tenant_id")
        required = ["nombre", "direccion", "precio", "stock", "proveedor"]

        if not tenant_id or not all(k in body for k in required):
            return {"statusCode": 400,
                    "body": json.dumps({"message": "Faltan campos obligatorios"})}

        id_producto    = str(uuid.uuid4())          # SK
        fecha_creacion = datetime.utcnow().isoformat(timespec="seconds")

        item = {
            "tenant_id"     : tenant_id,            # PK
            "id_producto"   : id_producto,          # SK
            "nombre"        : body["nombre"],
            "direccion"     : body["direccion"],
            "precio"        : body["precio"],
            "stock"         : body["stock"],
            "imagen_url"    : body.get("imagen_url", []),
            "fecha_creacion": fecha_creacion,
            "proveedor"     : body["proveedor"]
        }

        # ── 3) Guardar en DynamoDB ───────────────────────────
        table.put_item(Item=item)

        # ── 4) Respuesta ─────────────────────────────────────
        return {"statusCode": 201, "body": json.dumps(item)}

    except Exception as e:
        return {"statusCode": 500,
                "body": json.dumps({"error": str(e)})}
