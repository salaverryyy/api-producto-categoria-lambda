from dataclasses import dataclass
from domain.category import Category  # Asegúrate de importar correctamente el modelo Category

@dataclass
class CategoryDTO:
    id_categoria: int
    nombre: str
    descripcion: str

    @staticmethod
    def from_domain(cat: Category) -> 'CategoryDTO':
        """
        Convierte un Category (dominio) a CategoryDTO para la salida de la API.
        """
        return CategoryDTO(
            id_categoria=cat.id_categoria,
            nombre=cat.nombre,
            descripcion=cat.descripcion
        )

    def to_domain(self) -> Category:
        """
        Convierte este DTO a un Category (dominio), útil al crear/actualizar.
        """
        return Category(
            id_categoria=self.id_categoria,
            nombre=self.nombre,
            descripcion=self.descripcion
        )

    def to_dict(self) -> dict:
        """
        Convierte este DTO a un diccionario que pueda ser convertido a JSON
        para la respuesta de la API.
        """
        return {
            'id_categoria': self.id_categoria,
            'nombre': self.nombre,
            'descripcion': self.descripcion
        }

    @staticmethod
    def from_dict(data: dict) -> 'CategoryDTO':
        """
        Convierte un diccionario a un CategoryDTO.
        """
        return CategoryDTO(
            id_categoria=int(data['id_categoria']),
            nombre=data['nombre'],
            descripcion=data['descripcion']
        )
