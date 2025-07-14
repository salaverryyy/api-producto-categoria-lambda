import json, uuid, os, urllib.request, urllib.error, boto3
from datetime import datetime
from typing import cast

# ─── Recursos AWS ─────────────────────────────────────────────
dynamodb = boto3.resource("dynamodb")
table    = dynamodb.Table(os.environ["PRODUCTS_TABLE"])
categories_table = dynamodb.Table(os.environ["CATEGORIES_TABLE"])

VERIFY_TOKEN_URL: str = os.environ["VERIFY_TOKEN_URL"]

def _verify_token(token: str) -> bool:
    print("Verificando token:", token)
    req = urllib.request.Request(VERIFY_TOKEN_URL, method="GET")
    req.add_header("Authorization", f"Bearer {token}")

    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            print("Respuesta verificación token status:", r.status)
            return r.status == 200
    except urllib.error.HTTPError as e:
        print("HTTPError en verificación de token:", e)
        return False
    except Exception as e:
        print("Exception en verificación de token:", e)
        return False

def lambda_handler(event, context):
    try:
        print("Evento recibido:", event)
        # ── 1) Autenticación ─────────────────────────────────
        auth = (event.get("headers") or {}).get("Authorization")
        print("Header Authorization:", auth)
        if not auth:
            print("Token no proporcionado.")
            return {"statusCode": 401,
                    "body": json.dumps({"message": "Token no proporcionado"})}

        token = auth.split()[1]
        print("Token extraído:", token)
        if not _verify_token(token):
            print("Acceso no autorizado, token inválido.")
            return {"statusCode": 403,
                    "body": json.dumps({"message": "Acceso no autorizado"})}

        # ── 2) Datos de entrada ──────────────────────────────
        body = json.loads(event.get("body") or "{}")
        print("Body recibido:", body)
        tenant_id = body.get("tenant_id")
        categoria_nombre = body.get("categoria_nombre")
        required = ["nombre", "direccion", "precio", "stock", "proveedor", "categoria_nombre"]
        print("Campos requeridos:", required)

        if not tenant_id or not all(k in body for k in required):
            print("Faltan campos obligatorios.")
            return {"statusCode": 400,
                    "body": json.dumps({"message": "Faltan campos obligatorios"})}

        id_producto    = str(uuid.uuid4())
        fecha_creacion = datetime.utcnow().isoformat(timespec="seconds")
        print("id_producto generado:", id_producto)
        print("fecha_creacion:", fecha_creacion)

        item = {
            "tenant_id"     : tenant_id,
            "id_producto"   : id_producto,
            "nombre"        : body["nombre"],
            "direccion"     : body["direccion"],
            "precio"        : body["precio"],
            "stock"         : body["stock"],
            "imagen_url"    : body.get("imagen_url", []),
            "fecha_creacion": fecha_creacion,
            "proveedor"     : body["proveedor"],
            "categoria_nombre": categoria_nombre
        }
        print("Item a guardar en DynamoDB:", item)

        # ── 3) Guardar producto en DynamoDB ─────────────────
        table.put_item(Item=item)
        print("Producto guardado correctamente.")

        # ── 4) Crear categoría si no existe ─────────────────
        print("Buscando si la categoría ya existe...")
        resp = categories_table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key("tenant_id").eq(tenant_id)
        )
        categorias = resp.get("Items", [])
        categoria_existente = next((cat for cat in categorias if cat["nombre"] == categoria_nombre), None)

        if categoria_existente:
            print("La categoría ya existe:", categoria_existente)
            id_categoria = categoria_existente["id_categoria_producto"].split("#")[0]
        else:
            print("La categoría no existe, creando nueva categoría...")
            id_categoria = str(uuid.uuid4())

        id_categoria_producto = f"{id_categoria}#{id_producto}"
        categoria_item = {
            "tenant_id": tenant_id,
            "id_categoria_producto": id_categoria_producto,
            "nombre": categoria_nombre,
            "descripcion": body.get("categoria_descripcion", "")
        }
        categories_table.put_item(Item=categoria_item)
        print("Entrada de categoría creada:", categoria_item)

        # ── 5) Respuesta ─────────────────────────────────────
        return {"statusCode": 201, "body": json.dumps({
            "producto": item,
            "categoria": categoria_item
        })}

    except Exception as e:
        print("Error en lambda_handler:", str(e))
        return {"statusCode": 500,
                "body": json.dumps({"error": str(e)})}