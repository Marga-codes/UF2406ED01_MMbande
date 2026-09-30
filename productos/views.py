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

from django.contrib.auth.decorators import login_required
from django.contrib.auth import login

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

    # Aquí está la seguridad real del ejercicio 3.
    # Al añadir usuario=request.user a la consulta, Django busca un
    # producto que a la vez tenga esa id Y me pertenezca a mí.
    #
    # Si maría se inventa la url /productos/5/editar/ de un producto
    # de juan, no encuentra nada y devuelve 404: ni siquiera sabe que
    # el producto existe.
    producto = get_object_or_404(
        Producto,
        pk=pk,
        usuario=request.user
    )

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

            return redirect("mis_productos")

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

    # Mismo filtro que en la edición: propietario incluido.
    # Un usuario no puede borrar productos de otros ni siquiera
    # escribiendo la URL a mano.
    producto = get_object_or_404(
        Producto,
        pk=pk,
        usuario=request.user
    )

    if request.method == "POST":

        producto.delete()

        messages.success(
            request,
            "Producto eliminado correctamente."
        )

        return redirect("mis_productos")

    return render(
        request,
        "productos/eliminar.html",
        {
            "producto": producto
        }
    )
