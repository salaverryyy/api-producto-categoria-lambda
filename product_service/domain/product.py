from dataclasses import dataclass, field
from decimal import Decimal
from datetime import date
from typing import List

@dataclass
class Product:
    id_producto: int
    nombre: str
    direccion: str
    precio: Decimal
    stock: int
    proveedor: str
    category: str

    imagen_url: List[str] = field(default_factory=list)
    fecha_creacion: date = field(default_factory=date.today)

    def to_dict(self) -> dict:
        return {
            'id_producto': self.id_producto,
            'nombre': self.nombre,
            'direccion': self.direccion,
            'precio': str(self.precio),
            'stock': self.stock,
            'imagen_url': self.imagen_url,
            'fecha_creacion': self.fecha_creacion.isoformat(),
            'proveedor': self.proveedor,
            'category': self.category
        }

    @staticmethod
    def from_dict(data: dict) -> 'Product':
        return Product(
            id_producto=int(data['id_producto']),
            nombre=data['nombre'],
            direccion=data['direccion'],
            precio=Decimal(str(data['precio'])),
            stock=int(data['stock']),
            imagen_url=data.get('imagen_url', []),
            fecha_creacion=date.fromisoformat(data['fecha_creacion']),
            proveedor=data['proveedor'],
            category=data['category']
        )
