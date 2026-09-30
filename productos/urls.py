"""
URLs de la aplicación productos.

Aquí se empareja cada dirección del navegador con la vista que la atiende.
El nombre que lleva cada una (name="producto_lista"...) es el que
usamos luego con {% url %} en las plantillas y con redirect() en las vistas,
así que si cambiamos una URL solo tenemos que tocar este archivo.
"""

from django.urls import path

from . import views

urlpatterns = [

    # La raíz del sitio es la página de inicio.
    path(
        "",
        views.home,
        name="home"
    ),

    # Alta de usuarios.
    path(
        "register/",
        views.register,
        name="register"
    ),

    # ------------------------------------------------------------------
    # Categorías (todas protegidas con @login_required en la vista)
    # ------------------------------------------------------------------

    path(
        "categorias/",
        views.categoria_lista,
        name="categoria_lista"
    ),

    path(
        "categorias/nueva/",
        views.categoria_crear,
        name="categoria_crear"
    ),

    # <int:pk> coge el número de la URL y se lo pasa a la vista como pk.
    path(
        "categorias/<int:pk>/editar/",
        views.categoria_editar,
        name="categoria_editar"
    ),

    path(
        "categorias/<int:pk>/eliminar/",
        views.categoria_eliminar,
        name="categoria_eliminar"
    ),

    # ------------------------------------------------------------------
    # Productos
    # ------------------------------------------------------------------

    path(
        "productos/",
        views.producto_lista,
        name="producto_lista"
    ),

    # Detalle de un producto. El conversor <int:pk> solo acepta números,
    # así que esta ruta no se lleva por delante a /productos/nuevo/.
    path(
        "productos/<int:pk>/",
        views.producto_detalle,
        name="producto_detalle"
    ),

    path(
        "productos/nuevo/",
        views.producto_crear,
        name="producto_crear"
    ),

    path(
        "productos/<int:pk>/editar/",
        views.producto_editar,
        name="producto_editar"
    ),

    path(
        "productos/<int:pk>/eliminar/",
        views.producto_eliminar,
        name="producto_eliminar"
    ),
]
