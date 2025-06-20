from dataclasses import dataclass

@dataclass
class Category:
    id_categoria: int
    nombre: str
    descripcion: str

    def to_dict(self) -> dict:
        return {
            'id_categoria': self.id_categoria,
            'nombre': self.nombre,
            'descripcion': self.descripcion
        }

    @staticmethod
    def from_dict(data: dict) -> 'Category':
        return Category(
            id_categoria=int(data['id_categoria']),
            nombre=data['nombre'],
            descripcion=data['descripcion']
        )
