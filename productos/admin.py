"""
Registro de los modelos en el administrador de Django.

Sin estas líneas las categorías y los productos no aparecerían
en http://127.0.0.1:8000/admin/, aunque las tablas existan en la base de datos.

En este ejercicio vamos más allá de admin.site.register(): usamos
@admin.register con clases ModelAdmin para añadir columnas, filtros
y búsqueda, que es lo que convierte al admin en algo realmente útil.
"""

from django.contrib import admin

from .models import (
    Categoria,
    Producto,
)


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):

    # Columnas que se ven en el listado. Sin esto solo aparecería
    # "Categoria object (1)", que no ayuda a identificar nada.
    list_display = (
        "id",
        "nombre",
        "fecha_creacion",
    )

    # Cuadro de búsqueda por nombre en la barra superior del admin.
    search_fields = (
        "nombre",
    )


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):

    # Incluimos el propietario: en un admin es la primera pregunta
    # que uno se hace, "¿de quién es este producto?".
    list_display = (
        "id",
        "nombre",
        "categoria",
        "usuario",
        "precio",
        "fecha_creacion",
    )

    # Menús laterales para filtrar el listado por categoría o por
    # propietario. Muy práctico con pocos productos y con miles.
    list_filter = (
        "categoria",
        "usuario",
    )

    # Búsqueda. Ojo al doble guion bajo: "usuario__username" busca
    # dentro del campo username del usuario relacionado, igual que
    # "categoria__nombre" busca en el nombre de la categoría.
    search_fields = (
        "nombre",
        "usuario__username",
        "categoria__nombre",
    )
