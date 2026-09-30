"""
Modelos de la aplicación productos.

Aquí definimos las dos tablas de la base de datos:

- Categoria: nombre, descripción y cuándo se creó.
- Producto:  lo mismo, más el precio y la categoría a la que pertenece.

La relación es de uno a muchos:

    Categoria 1 -------- N Producto

Una categoría puede tener muchos productos,
y un producto solamente pertenece a una categoría.
"""

from django.db import models


class Categoria(models.Model):
    # Nombre corto, como "Ropa" o "Electrónica".
    nombre = models.CharField(max_length=100)

    # Texto libre para explicar qué guarda esta categoría.
    # blank=True significa que no es obligatorio rellenarlo.
    descripcion = models.TextField(blank=True)

    # La fecha se rellena sola en el momento en que se crea el registro,
    # y ya no se vuelve a tocar. Para eso sirve auto_now_add.
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # Esto es lo que Django muestra por pantalla cuando tiene que
        # representar una categoría (en el admin, en los desplegables...).
        # Sin él saldría algo como "Categoria object (1)", que no ayuda.
        return self.nombre


class Producto(models.Model):
    nombre = models.CharField(max_length=150)

    descripcion = models.TextField(blank=True)

    # Un precio con decimales: hasta 10 dígitos en total
    # y 2 de ellos después de la coma. Usamos Decimal y no float
    # porque con el dinero no se puede perder precisión.
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    # Aquí está la relación con la categoría.
    # on_delete=models.CASCADE quiere decir que, si borramos la categoría,
    # se borran también los productos que tenía. Es la opción que pide
    # el enunciado (y la que avisa el formulario de eliminar categoría).
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.CASCADE,
        related_name="productos"
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # El nombre del producto es lo más útil para mostrarlo en listas.
        return self.nombre
