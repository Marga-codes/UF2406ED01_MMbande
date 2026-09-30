"""
URLs principales del proyecto tienda.

Aquí se decide qué carpeta se encarga de cada trozo de la web:

- /admin/       -> el panel de administración de Django.
- /             -> las URLs de nuestra app productos (home, CRUD, registro...).
- /accounts/    -> las rutas de autenticación que Django trae de serie
                   (login, logout y todo el tema de recuperar contraseña).
"""

from django.contrib import admin

from django.urls import (
    path,
    include,
)

urlpatterns = [

    # El panel de administración, siempre disponible en /admin/.
    path(
        'admin/',
        admin.site.urls
    ),

    # Todo lo demás lo gestiona nuestra aplicación.
    # Al incluirlas en la raíz, el home queda en http://127.0.0.1:8000/
    # y el listado de productos en /productos/, y así sucesivamente.
    path(
        '',
        include('productos.urls')
    ),

    # Django trae montado todo el sistema de autenticación.
    # Con esta sola línea tenemos disponibles:
    #   /accounts/login/
    #   /accounts/logout/
    #   /accounts/password_reset/
    #   /accounts/password_reset/done/
    #   /accounts/reset/<uidb64>/<token>/
    #   /accounts/reset/done/
    # Por eso no hacemos vistas de login ni de reset a mano:
    # solo tenemos que crear las plantillas que las acompañan.
    path(
        'accounts/',
        include('django.contrib.auth.urls')
    ),

]
