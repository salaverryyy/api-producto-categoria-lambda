from dataclasses import dataclass
from decimal import Decimal
from datetime import date  # Asegúrate de importar date correctamente
from domain.product import Product

@dataclass
class ProductDTO:
    id_producto: int
    nombre: str
    direccion: str
    precio: Decimal
    stock: int
    proveedor: str
    category: str

    imagen_url: list
    fecha_creacion: str  # Lo mantenemos como un string (ISO format)
    
    @staticmethod
    def from_domain(prod: Product) -> 'ProductDTO':
        """
        Convierte un Product (dominio) a ProductDTO para la salida de la API.
        """
        return ProductDTO(
            id_producto=prod.id_producto,
            nombre=prod.nombre,
            direccion=prod.direccion,
            precio=prod.precio,
            stock=prod.stock,
            proveedor=prod.proveedor,
            imagen_url=prod.imagen_url,
            fecha_creacion=prod.fecha_creacion.isoformat(),  # Convertimos `date` a `str`
            category=prod.category
        )

    @staticmethod
    def from_dict(data: dict) -> 'ProductDTO':
        """
        Convierte un diccionario a un ProductDTO.
        """
        return ProductDTO(
            id_producto=int(data['id_producto']),
            nombre=data['nombre'],
            direccion=data['direccion'],
            precio=Decimal(str(data['precio'])),
            stock=int(data['stock']),
            imagen_url=data.get('imagen_url', []),
            fecha_creacion=data['fecha_creacion'],  # Mantener como string
            proveedor=data['proveedor'],
            category=data['category_id']
        )

    def to_domain(self) -> Product:
        """
        Convierte este DTO a un Product (dominio), útil al crear/actualizar.
        """
        return Product(
            id_producto=self.id_producto,
            nombre=self.nombre,
            direccion=self.direccion,
            precio=self.precio,
            stock=self.stock,
            proveedor=self.proveedor,
            imagen_url=self.imagen_url,
            fecha_creacion=date.fromisoformat(self.fecha_creacion),  # Convertimos de `str` a `date`
            category=self.category
        )

    def to_dict(self) -> dict:
        """
        Convierte este DTO a un diccionario que pueda ser convertido a JSON
        para la respuesta de la API.
        """
        return {
            'id_producto': self.id_producto,
            'nombre': self.nombre,
            'direccion': self.direccion,
            'precio': str(self.precio),  # Convierte Decimal a string para JSON
            'stock': self.stock,
            'imagen_url': self.imagen_url,
            'fecha_creacion': self.fecha_creacion,
            'proveedor': self.proveedor,
            'category': self.category
        }
