"""
Vistas de la aplicación productos.

Una vista es sencillamente la función que decide qué devolver Django
cuando alguien entra en una dirección concreta.

Orden del archivo:

1.  home                -> página de inicio
2.  register            -> alta de usuarios
3.  CRUD de categorías  -> listar, crear, editar y eliminar
4.  CRUD de productos   -> listar, detalle, crear, editar y eliminar

Ojo: el login, el logout y la recuperación de contraseña NO están aquí.
Esos los trae Django montados con 'django.contrib.auth.urls' en tienda/urls.py.
"""

# messages es el sistema de avisos de Django: guardamos un texto en la
# sesión y se muestra una sola vez, en la página a la que redirigimos.
# base.html se encarga de pintarlo como una alerta de Bootstrap.
from django.contrib import messages

# PermissionDenied es la excepción que Django traduce en un 403 Forbidden.
# La usamos cuando alguien intenta tocar un producto que no es suyo.
from django.core.exceptions import PermissionDenied

from django.contrib.auth.decorators import login_required
from django.contrib.auth import login

# User lo necesitamos en el panel de administración, para listar cuentas.
from django.contrib.auth.models import User

# staff_member_required deja pasar solo a usuarios con is_staff=True
# (los demás ni siquiera llegan a ver la vista).
from django.contrib.admin.views.decorators import staff_member_required

from django.shortcuts import (
    render,
    redirect,
    get_object_or_404,
)

from .models import Categoria, Producto

from .forms import (
    RegistroForm,
    CategoriaForm,
    ProductoForm,
)

# Las reglas de quién puede qué viven en permissions.py.
# Aquí solo las consultamos.
from .permissions import (
    puede_editar_producto,
    puede_eliminar_producto,
)


# ----------------------------------------------------------------------
# 11. Página principal
# ----------------------------------------------------------------------
def home(request):
    # La más sencilla de todas: no toca la base de datos, solo pinta plantilla.
    return render(request, "home.html")


# ----------------------------------------------------------------------
# 12. Registro de usuarios
# ----------------------------------------------------------------------
def register(request):

    # Si quien entra ya tiene sesión abierta, no tiene sentido que se
    # registre otra vez, así que lo mandamos al inicio.
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":

        # El usuario ha rellenado el formulario y ha pulsado el botón:
        # llegan los datos y comprobamos que estén bien.
        form = RegistroForm(request.POST)

        if form.is_valid():

            # Si todo está correcto, guardamos el usuario nuevo...
            usuario = form.save()

            # ...lo dejamos logueado automáticamente (no hace falta
            # que vuelva a escribir su contraseña)...
            login(request, usuario)

            # Aviso de éxito. Ojo: no se pinta aquí, se guarda para
            # la siguiente página, porque justo ahora redirigimos.
            messages.success(
                request,
                "Usuario registrado correctamente."
            )

            # ...y lo mandamos a la página principal.
            return redirect("home")

        # Si el formulario no está válido (email repetido, contraseña
        # demasiado débil...) lo decimos con un mensaje de error;
        # los detalles de cada campo siguen saliendo bajo cada input.
        messages.error(
            request,
            "Revisa los datos del formulario."
        )

    else:

        # Todavía no ha escrito nada: mostramos el formulario en blanco.
        form = RegistroForm()

    return render(
        request,
        "registration/register.html",
        {
            "form": form
        }
    )


# ----------------------------------------------------------------------
# 13. CRUD de categorías
# ----------------------------------------------------------------------
# Listar categorías
@login_required
def categoria_lista(request):

    # Todas las categorías, tal y como están en la base de datos.
    categorias = Categoria.objects.all()

    return render(
        request,
        "categorias/lista.html",
        {
            "categorias": categorias
        }
    )


# Crear categoría
@login_required
def categoria_crear(request):

    if request.method == "POST":

        form = CategoriaForm(request.POST)

        if form.is_valid():

            # El formulario ya valida que el nombre no esté vacío:
            # si pasa, guardamos la categoría nueva en la base de datos.
            form.save()

            messages.success(
                request,
                "Categoría creada correctamente."
            )

            # Y volvemos a la lista para verla aparecer.
            return redirect("categoria_lista")

    else:

        form = CategoriaForm()

    return render(
        request,
        "categorias/formulario.html",
        {
            "form": form,
            "titulo": "Nueva categoría",
        }
    )


# Editar categoría
@login_required
def categoria_editar(request, pk):

    # pk es el identificador que viene en la URL, algo como
    # /categorias/3/editar/ -> pk = 3.
    # Si no existe, en vez de romperse devuelve un 404 decente.
    categoria = get_object_or_404(
        Categoria,
        pk=pk
    )

    if request.method == "POST":

        # Fíjate en instance=categoria: sin eso Django crearía una
        # categoría nueva; con él, actualiza la que ya teníamos.
        form = CategoriaForm(
            request.POST,
            instance=categoria
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Categoría actualizada correctamente."
            )

            return redirect("categoria_lista")

    else:

        # GET: mostramos el formulario ya relleno con los datos actuales.
        form = CategoriaForm(
            instance=categoria
        )

    return render(
        request,
        "categorias/formulario.html",
        {
            "form": form,
            "titulo": "Editar categoría",
        }
    )


# Eliminar categoría
@login_required
def categoria_eliminar(request, pk):

    categoria = get_object_or_404(
        Categoria,
        pk=pk
    )

    if request.method == "POST":

        # Solo se borra si el usuario confirma con POST.
        # Un enlace normal (GET) no debería borrar nada nunca.
        categoria.delete()

        messages.success(
            request,
            "Categoría eliminada correctamente."
        )

        # Ojo: al borrar la categoría se borran también sus productos,
        # porque la relación es CASCADE. Por eso el aviso en la plantilla.
        return redirect("categoria_lista")

    # Si todavía no ha confirmado, mostramos la pantalla de aviso.
    return render(
        request,
        "categorias/eliminar.html",
        {
            "categoria": categoria
        }
    )


# ----------------------------------------------------------------------
# 14. CRUD de productos
# ----------------------------------------------------------------------
# Listar productos
def producto_lista(request):

    # Esta vista no lleva @login_required: el catálogo es público,
    # cualquiera puede ver los productos sin entrar.
    #
    # select_related("categoria", "usuario") trae la categoría y el
    # propietario en la misma consulta, así evitamos una consulta extra
    # por producto al pintar la lista.
    #
    # order_by("-fecha_creacion"): los más nuevos primero.
    productos = Producto.objects.select_related(
        "categoria",
        "usuario",
    ).order_by("-fecha_creacion")

    return render(
        request,
        "productos/lista.html",
        {
            "productos": productos
        }
    )


# Detalle de un producto
def producto_detalle(request, pk):

    # Vista pública también: solo lectura. Traemos el propietario
    # junto al producto para poder mostrar "Propietario: ..." y para
    # comparar en la plantilla si quien mira es el dueño.
    producto = get_object_or_404(
        Producto.objects.select_related(
            "categoria",
            "usuario",
        ),
        pk=pk
    )

    return render(
        request,
        "productos/detalle.html",
        {
            "producto": producto
        }
    )


# Crear producto
@login_required
def producto_crear(request):

    if request.method == "POST":

        form = ProductoForm(request.POST)

        if form.is_valid():

            # commit=False crea el objeto en memoria sin guardarlo todavía.
            # Es el truco que nos deja rellenar el campo usuario, que no
            # viene en el formulario: nadie podría enviarlo a mano.
            producto = form.save(
                commit=False
            )

            # El propietario es quien está logueado, no lo elige nadie.
            producto.usuario = request.user

            # Ya con el dueño puesto, sí lo guardamos en la base de datos.
            producto.save()

            messages.success(
                request,
                "Producto creado correctamente."
            )

            # Volvemos a "Mis productos", que es donde aparece el recién
            # creado y donde solo se listan los del usuario actual.
            return redirect("mis_productos")

    else:

        form = ProductoForm()

    return render(
        request,
        "productos/formulario.html",
        {
            "form": form,
            "titulo": "Nuevo producto",
        }
    )


# ----------------------------------------------------------------------
# "Mis productos": el listado privado de lo que ha creado cada cual
# ----------------------------------------------------------------------
@login_required
def mis_productos(request):

    # filter(usuario=request.user) es la clave de esta página:
    # solo los productos cuyo propietario soy yo. Sin esa condición
    # saldrían todos los de la base de datos.
    productos = Producto.objects.filter(
        usuario=request.user
    ).select_related(
        "categoria"
    ).order_by(
        "-fecha_creacion"
    )

    return render(
        request,
        "productos/mis_productos.html",
        {
            "productos": productos
        }
    )


# Editar producto
@login_required
def producto_editar(request, pk):

    # Primero localizamos el producto sin más: ya no filtramos por
    # usuario aquí, porque el administrador también tiene que poder
    # llegar a productos ajenos.
    producto = get_object_or_404(
        Producto,
        pk=pk
    )

    # Y aquí está la comprobación de permisos del ejercicio 4.
    # Si no es el dueño ni is_staff, lanzamos PermissionDenied,
    # que Django convierte en un 403 Forbidden con nuestra plantilla.
    #
    # Fíjate en que esto va en el SERVIDOR: ocultar el botón en la
    # plantilla no serviría de nada, cualquiera puede escribir la URL.
    if not puede_editar_producto(
        request.user,
        producto
    ):
        raise PermissionDenied

    if request.method == "POST":

        form = ProductoForm(
            request.POST,
            instance=producto
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Producto actualizado correctamente."
            )

            # Volvemos al listado general: desde aquí también puede
            # haber llegado el administrador, editando un producto
            # que no es suyo, y "Mis productos" no lo mostraría.
            return redirect("producto_lista")

    else:

        form = ProductoForm(
            instance=producto
        )

    return render(
        request,
        "productos/formulario.html",
        {
            "form": form,
            "titulo": "Editar producto",
        }
    )


# Eliminar producto
@login_required
def producto_eliminar(request, pk):

    producto = get_object_or_404(
        Producto,
        pk=pk
    )

    # Mismo esquema que en la edición: dueño o administrador.
    # Un usuario normal no puede borrar productos ajenos ni siquiera
    # enviando el formulario con POST a mano.
    if not puede_eliminar_producto(
        request.user,
        producto
    ):
        raise PermissionDenied

    if request.method == "POST":

        producto.delete()

        messages.success(
            request,
            "Producto eliminado correctamente."
        )

        # Igual que al editar: al listado general.
        return redirect("producto_lista")

    return render(
        request,
        "productos/eliminar.html",
        {
            "producto": producto
        }
    )


# ----------------------------------------------------------------------
# Panel interno de administración (solo usuarios staff)
# ----------------------------------------------------------------------
@staff_member_required
def panel_admin(request):

    # El decorador hace todo el trabajo de control de acceso:
    # si quien entra no tiene is_staff, ni llega a esta función
    # (lo manda al login de /admin/).
    #
    # Es un panel informativo con vistas rápidas: cuántos usuarios y
    # productos hay, y la lista completa con su propietario.
    productos = Producto.objects.select_related(
        "categoria",
        "usuario",
    ).order_by(
        "-fecha_creacion"
    )

    usuarios = User.objects.all().order_by(
        "username"
    )

    context = {
        "productos": productos,
        "usuarios": usuarios,
    }

    return render(
        request,
        "administracion/panel.html",
        context
    )
