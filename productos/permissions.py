"""
Reglas de permisos de la aplicación, centralizadas en un solo sitio.

La lógica es sencilla:

- un usuario normal solo gestiona SUS productos;
- el administrador (is_staff) gestiona cualquiera.

Al tenerla aquí, las vistas no se llenan de condiciones repetidas y,
si mañana cambia la regla (por ejemplo, añadiendo el rol "editor"),
se toca un único archivo.

Ojo con lo que NO es esto: en las plantillas también comprobamos
permisos para decidir si pintar botones, pero eso es solo comodidad
visual. La seguridad real es esta, comprobada en el servidor.
"""


def puede_editar_producto(user, producto):
    """¿Puede `user` editar el `producto` dado?"""

    # Sin sesión no se edita nada, ni lo propio.
    if not user.is_authenticated:
        return False

    # El administrador de la aplicación pasa siempre.
    if user.is_staff:
        return True

    # El resto: solo si el producto es suyo.
    return producto.usuario == user


def puede_eliminar_producto(user, producto):
    """¿Puede `user` eliminar el `producto` dado?"""

    # Misma regla que la edición. Se dejan como dos funciones
    # distintas aunque coincidan hoy: si algún día borrar es más
    # restrictivo que editar (pensemos en un editor que puede
    # corregir pero no borrar), cada una evoluciona por su lado.
    if not user.is_authenticated:
        return False

    if user.is_staff:
        return True

    return producto.usuario == user
