"""
Registro de los modelos en el administrador de Django.

Sin estas dos líneas las categorías y los productos no aparecerían
en http://127.0.0.1:8000/admin/, aunque las tablas existan en la base de datos.
"""

from django.contrib import admin
from .models import Categoria, Producto

# Los damos de alta para poder consultarlos, crearlos y borrarlos desde el admin.
admin.site.register(Categoria)
admin.site.register(Producto)
