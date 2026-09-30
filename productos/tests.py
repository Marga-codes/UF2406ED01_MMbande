"""
Tests de la práctica.

Comprueban lo que pide el enunciado: que cada página se renderice,
que las vistas privadas redirigan al login, que el CRUD funcione de
principio a fin y que el registro y el reset de contraseña trabajan
como se espera.

Se ejecutan con:

    python manage.py test
"""

from decimal import Decimal

from django.contrib.auth.models import AnonymousUser, User
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from .models import Categoria, Producto
from .permissions import puede_editar_producto, puede_eliminar_producto


class DatosDePrueba:
    """Atajos para crear los objetos que usan casi todos los tests."""

    @staticmethod
    def categoria(nombre="Informática", descripcion="Equipos"):
        return Categoria.objects.create(
            nombre=nombre,
            descripcion=descripcion,
        )

    @staticmethod
    def producto(categoria, usuario, nombre="Portátil", precio="799.99"):
        # El propietario es obligatorio desde el ejercicio 3:
        # sin él Django no deja guardar el producto.
        return Producto.objects.create(
            nombre=nombre,
            descripcion="Portátil para estudiante.",
            precio=Decimal(precio),
            categoria=categoria,
            usuario=usuario,
        )

    @staticmethod
    def usuario(username="juan", email="juan@email.com"):
        return User.objects.create_user(
            username=username,
            email=email,
            password="UnaClaveSegura2026!",
        )


# ----------------------------------------------------------------------
# Páginas públicas: tienen que cargar sin sesión y sin errores de plantilla
# ----------------------------------------------------------------------
class VistasPublicasTests(TestCase):

    def test_pagina_principal(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home.html")

    def test_listado_de_productos(self):
        cat = DatosDePrueba.categoria()
        DatosDePrueba.producto(cat, DatosDePrueba.usuario())

        response = self.client.get(reverse("producto_lista"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "productos/lista.html")
        # El producto creado tiene que aparecer en la página.
        self.assertContains(response, "Portátil")

    def test_detalle_de_producto(self):
        cat = DatosDePrueba.categoria()
        producto = DatosDePrueba.producto(cat, DatosDePrueba.usuario())

        response = self.client.get(
            reverse("producto_detalle", args=[producto.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "productos/detalle.html")

    def test_detalle_inexistente_da_404(self):
        response = self.client.get(
            reverse("producto_detalle", args=[999])
        )
        self.assertEqual(response.status_code, 404)

    def test_login_y_registro_cargan(self):
        self.assertEqual(
            self.client.get(reverse("login")).status_code, 200
        )
        self.assertEqual(
            self.client.get(reverse("register")).status_code, 200
        )


# ----------------------------------------------------------------------
# Protección de vistas: sin sesión no se entra a ninguna de categorías
# ----------------------------------------------------------------------
class VistasProtegidasTests(TestCase):

    def test_categorias_redirige_al_login(self):
        response = self.client.get(reverse("categoria_lista"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.headers["Location"])

    def test_producto_nuevo_tambien_pide_login(self):
        response = self.client.get(reverse("producto_crear"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.headers["Location"])


# ----------------------------------------------------------------------
# CRUD de categorías, ya con la sesión abierta
# ----------------------------------------------------------------------
class CrudCategoriasTests(TestCase):

    def setUp(self):
        self.usuario = DatosDePrueba.usuario()
        self.client.force_login(self.usuario)

    def test_listar(self):
        DatosDePrueba.categoria()

        response = self.client.get(reverse("categoria_lista"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "categorias/lista.html")
        self.assertContains(response, "Informática")

    def test_crear_muestra_el_mensaje_de_exito(self):
        response = self.client.post(
            reverse("categoria_crear"),
            {"nombre": "Oficina", "descripcion": "Material"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Categoria.objects.filter(nombre="Oficina").exists()
        )
        # messages.success de la vista tiene que salir como alerta.
        self.assertContains(response, "Categoría creada correctamente.")

    def test_editar(self):
        categoria = DatosDePrueba.categoria()

        response = self.client.post(
            reverse("categoria_editar", args=[categoria.pk]),
            {"nombre": "Electrónica", "descripcion": "Cambiado"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        categoria.refresh_from_db()
        self.assertEqual(categoria.nombre, "Electrónica")
        self.assertContains(response, "Categoría actualizada correctamente.")

    def test_eliminar_con_post(self):
        categoria = DatosDePrueba.categoria()

        response = self.client.post(
            reverse("categoria_eliminar", args=[categoria.pk]),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Categoria.objects.filter(pk=categoria.pk).exists())

    def test_eliminar_get_no_borra_nada(self):
        # Un GET (por ejemplo un enlace en una web) no debe borrar nada.
        categoria = DatosDePrueba.categoria()

        self.client.get(
            reverse("categoria_eliminar", args=[categoria.pk])
        )

        self.assertTrue(Categoria.objects.filter(pk=categoria.pk).exists())


# ----------------------------------------------------------------------
# CRUD de productos
# ----------------------------------------------------------------------
class CrudProductosTests(TestCase):

    def setUp(self):
        self.usuario = DatosDePrueba.usuario()
        self.client.force_login(self.usuario)
        self.categoria = DatosDePrueba.categoria()

    def test_crear(self):
        response = self.client.post(
            reverse("producto_crear"),
            {
                "nombre": "Ratón",
                "descripcion": "Inalámbrico",
                "precio": "12.50",
                "categoria": self.categoria.pk,
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Producto.objects.filter(nombre="Ratón").exists()
        )
        self.assertContains(response, "Producto creado correctamente.")

    def test_editar(self):
        producto = DatosDePrueba.producto(self.categoria, self.usuario)

        response = self.client.post(
            reverse("producto_editar", args=[producto.pk]),
            {
                "nombre": "Portátil Lenovo",
                "descripcion": "Actualizado",
                "precio": "849.99",
                "categoria": self.categoria.pk,
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        producto.refresh_from_db()
        self.assertEqual(producto.nombre, "Portátil Lenovo")
        self.assertEqual(producto.precio, Decimal("849.99"))

    def test_eliminar(self):
        producto = DatosDePrueba.producto(self.categoria, self.usuario)

        response = self.client.post(
            reverse("producto_eliminar", args=[producto.pk]),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Producto.objects.filter(pk=producto.pk).exists())
        self.assertContains(response, "Producto eliminado correctamente.")

    def test_precio_invalido_no_guarda(self):
        response = self.client.post(
            reverse("producto_crear"),
            {
                "nombre": "Precio mal",
                "descripcion": "",
                "precio": "no-es-un-precio",
                "categoria": self.categoria.pk,
            },
        )

        # Vuelve a pintar el formulario con el error, sin guardar.
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Producto.objects.filter(nombre="Precio mal").exists())


# ----------------------------------------------------------------------
# Registro de usuarios
# ----------------------------------------------------------------------
class RegistroTests(TestCase):

    def test_registro_valido_crea_y_loguea(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "ana",
                "email": "ana@email.com",
                "password1": "UnaClaveSegura2026!",
                "password2": "UnaClaveSegura2026!",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username="ana").exists())
        self.assertContains(response, "Usuario registrado correctamente.")
        # Como queda logueado, la página de inicio lo saluda.
        self.assertContains(response, "ana")

    def test_email_repetido_no_deja_registrar(self):
        DatosDePrueba.usuario()  # juan@email.com ya existe

        response = self.client.post(
            reverse("register"),
            {
                "username": "otro",
                "email": "JUAN@email.com",  # misma cuenta, otras mayúsculas
                "password1": "UnaClaveSegura2026!",
                "password2": "UnaClaveSegura2026!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="otro").exists())
        self.assertFormError(
            response.context["form"],
            "email",
            "Ya existe un usuario con este email.",
        )

    def test_si_ya_hay_sesion_redirige_al_inicio(self):
        DatosDePrueba.usuario()
        self.client.force_login(User.objects.get(username="juan"))

        response = self.client.get(reverse("register"))

        self.assertEqual(response.status_code, 302)


# ----------------------------------------------------------------------
# Recuperación de contraseña con el flujo completo de Django
# ----------------------------------------------------------------------
class RecuperarContrasenaTests(TestCase):

    def setUp(self):
        self.usuario = DatosDePrueba.usuario()

    def test_solicitar_reset_envia_un_correo(self):
        response = self.client.post(
            reverse("password_reset"),
            {"email": "juan@email.com"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        # En los tests el correo va a una bandeja en memoria:
        # comprobamos que se creó exactamente uno.
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("juan@email.com", mail.outbox[0].to)

    def test_reset_sin_cuenta_tampoco_delata_nada(self):
        # No se dice que el correo no exista; simplemente no se envía nada.
        self.client.post(
            reverse("password_reset"),
            {"email": "nadie@email.com"},
        )

        self.assertEqual(len(mail.outbox), 0)

    def test_pantalla_de_confirmacion_invalida(self):
        response = self.client.get(
            reverse("password_reset_confirm", args=["MQ", "token-falso"])
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "registration/password_reset_confirm.html"
        )
        # Con el enlace inválido sale el aviso, no el formulario.
        self.assertContains(response, "El enlace no es válido")

    def test_pantalla_final(self):
        response = self.client.get(reverse("password_reset_complete"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Contraseña actualizada")

    def test_cambiar_contraseña_de_verdad(self):
        # Pedimos el reset de verdad para obtener uid y token reales.
        self.client.post(
            reverse("password_reset"),
            {"email": "juan@email.com"},
        )
        url = mail.outbox[0].body.split("http://testserver")[1].split()[0]

        # Como hace un navegador: primero GET al enlace. Django guarda
        # el token en la sesión y redirige a una URL sin el token,
        # para que no se filtre por la cabecera Referer.
        respuesta = self.client.get(url)
        self.assertEqual(respuesta.status_code, 302)
        url_formulario = respuesta.headers["Location"]

        # El POST se manda a esa URL limpia, que es donde está el formulario.
        response = self.client.post(
            url_formulario,
            {
                "new_password1": "OtraClaveSegura2026!",
                "new_password2": "OtraClaveSegura2026!",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Contraseña actualizada")
        # La contraseña nueva funciona y la vieja ya no.
        self.assertTrue(
            self.client.login(
                username="juan", password="OtraClaveSegura2026!"
            )
        )


# ----------------------------------------------------------------------
# Ejercicio 3: propiedad de los productos y control de permisos
# ----------------------------------------------------------------------
class PropiedadDeProductosTests(TestCase):

    def setUp(self):
        self.juan = DatosDePrueba.usuario("juan", "juan@email.com")
        self.maria = DatosDePrueba.usuario("maria", "maria@email.com")
        self.categoria = DatosDePrueba.categoria()
        self.producto_de_juan = DatosDePrueba.producto(
            self.categoria, self.juan, nombre="Portátil"
        )

    def test_crear_producto_asigna_como_dueno_a_request_user(self):
        # Juan crea un producto: el propietario tiene que ser él,
        # sin que el formulario permita elegirlo.
        self.client.force_login(self.juan)

        self.client.post(
            reverse("producto_crear"),
            {
                "nombre": "Monitor",
                "descripcion": "24 pulgadas",
                "precio": "149.99",
                "categoria": self.categoria.pk,
                # Por mucho que alguien meta "usuario" a mano en el
                # POST, el formulario lo ignora: no está en fields.
                "usuario": self.maria.pk,
            },
        )

        producto = Producto.objects.get(nombre="Monitor")
        self.assertEqual(producto.usuario, self.juan)

    def test_tras_crear_te_manda_a_mis_productos(self):
        self.client.force_login(self.juan)

        respuesta = self.client.post(
            reverse("producto_crear"),
            {
                "nombre": "Teclado",
                "descripcion": "mecánico",
                "precio": "39.99",
                "categoria": self.categoria.pk,
            },
            follow=False,
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assertIn(reverse("mis_productos"), respuesta.headers["Location"])

    def test_mis_productos_solo_los_mios(self):
        DatosDePrueba.producto(self.categoria, self.maria, nombre="Ratón")
        self.client.force_login(self.maria)

        respuesta = self.client.get(reverse("mis_productos"))

        self.assertEqual(respuesta.status_code, 200)
        self.assertTemplateUsed(response=respuesta, template_name="productos/mis_productos.html")
        # Lo suyo aparece...
        self.assertContains(respuesta, "Ratón")
        # ...y el de otros no.
        self.assertNotContains(respuesta, "Portátil")

    def test_mis_productos_pide_login(self):
        respuesta = self.client.get(reverse("mis_productos"))

        self.assertEqual(respuesta.status_code, 302)
        self.assertIn(reverse("login"), respuesta.headers["Location"])

    def test_listado_general_muestra_a_todos_los_duenos(self):
        # El catálogo es público y completo: se ven productos de
        # varios autores, con su propietario.
        respuesta = self.client.get(reverse("producto_lista"))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Portátil")
        self.assertContains(respuesta, "Publicado por:")
        self.assertContains(respuesta, "juan")

    def test_otro_usuario_no_puede_editar_mi_producto(self):
        # María teclea la URL a mano. El producto existe, así que
        # ahora ya no es un 404: es un 403 Forbidden porque no es
        # suyo ni es staff. Nuestra plantilla 403.html lo pinta.
        self.client.force_login(self.maria)

        respuesta = self.client.get(
            reverse("producto_editar", args=[self.producto_de_juan.pk])
        )

        self.assertEqual(respuesta.status_code, 403)
        self.assertTemplateUsed(respuesta, "403.html")

    def test_otro_usuario_no_puede_editar_mi_producto_con_post(self):
        self.client.force_login(self.maria)

        respuesta = self.client.post(
            reverse("producto_editar", args=[self.producto_de_juan.pk]),
            {
                "nombre": "Hackeado",
                "descripcion": "",
                "precio": "1.00",
                "categoria": self.categoria.pk,
            },
        )

        self.assertEqual(respuesta.status_code, 403)
        self.producto_de_juan.refresh_from_db()
        self.assertEqual(self.producto_de_juan.nombre, "Portátil")

    def test_otro_usuario_no_puede_eliminar_mi_producto(self):
        # Tampoco borra: mismo control de permisos en la vista.
        self.client.force_login(self.maria)

        respuesta = self.client.post(
            reverse("producto_eliminar", args=[self.producto_de_juan.pk])
        )

        self.assertEqual(respuesta.status_code, 403)
        self.assertTrue(
            Producto.objects.filter(pk=self.producto_de_juan.pk).exists()
        )

    def test_el_dueno_si_puede_editar_y_borrar(self):
        self.client.force_login(self.juan)

        respuesta = self.client.post(
            reverse("producto_editar", args=[self.producto_de_juan.pk]),
            {
                "nombre": "Portátil Lenovo",
                "descripcion": "Actualizado",
                "precio": "849.99",
                "categoria": self.categoria.pk,
            },
        )

        self.assertEqual(respuesta.status_code, 302)
        self.producto_de_juan.refresh_from_db()
        self.assertEqual(self.producto_de_juan.nombre, "Portátil Lenovo")

    def test_botones_ocultos_para_los_ajenos(self):
        # Interfaz, no seguridad: quien no es el dueño ni siquiera
        # ve los enlaces de editar y eliminar en el detalle.
        self.client.force_login(self.maria)

        respuesta = self.client.get(
            reverse("producto_detalle", args=[self.producto_de_juan.pk])
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Propietario:")
        self.assertNotContains(respuesta, reverse("producto_editar", args=[self.producto_de_juan.pk]))

    def test_el_dueno_si_ve_los_botones(self):
        self.client.force_login(self.juan)

        respuesta = self.client.get(
            reverse("producto_detalle", args=[self.producto_de_juan.pk])
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, reverse("producto_editar", args=[self.producto_de_juan.pk]))

    def test_el_detalle_es_publico(self):
        # Cualquiera, sin sesión, ve la ficha y al propietario.
        respuesta = self.client.get(
            reverse("producto_detalle", args=[self.producto_de_juan.pk])
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Propietario:")
        self.assertContains(respuesta, "juan")

    def test_home_cuenta_tus_productos(self):
        self.client.force_login(self.juan)

        respuesta = self.client.get(reverse("home"))

        self.assertEqual(respuesta.status_code, 200)
        # Tiene uno propio en setUp.
        self.assertContains(respuesta, "producto(s)")


# ----------------------------------------------------------------------
# Ejercicio 4: roles y permisos
# ----------------------------------------------------------------------
class RolesYPermisosTests(TestCase):

    def setUp(self):
        self.juan = DatosDePrueba.usuario("juan", "juan@email.com")
        self.maria = DatosDePrueba.usuario("maria", "maria@email.com")

        # El administrador de la práctica es simplemente una cuenta
        # con is_staff=True. No hace falta que sea superusuario.
        self.admin = DatosDePrueba.usuario("admin", "admin@email.com")
        self.admin.is_staff = True
        self.admin.save()

        self.categoria = DatosDePrueba.categoria()
        self.producto_de_juan = DatosDePrueba.producto(
            self.categoria, self.juan, nombre="Portátil"
        )

    # ------------------------------------------------------------------
    # Las funciones de permissions.py, probadas en aislamiento
    # ------------------------------------------------------------------
    def test_regla_de_permisos(self):
        # Sin sesión no se edita ni se borra nada.
        anonimo = AnonymousUser()
        self.assertFalse(puede_editar_producto(anonimo, self.producto_de_juan))
        self.assertFalse(puede_eliminar_producto(anonimo, self.producto_de_juan))

        # Otro usuario normal tampoco.
        self.assertFalse(puede_editar_producto(self.maria, self.producto_de_juan))
        self.assertFalse(puede_eliminar_producto(self.maria, self.producto_de_juan))

        # El dueño, sí.
        self.assertTrue(puede_editar_producto(self.juan, self.producto_de_juan))
        self.assertTrue(puede_eliminar_producto(self.juan, self.producto_de_juan))

        # Y el administrador, con cualquier producto.
        self.assertTrue(puede_editar_producto(self.admin, self.producto_de_juan))
        self.assertTrue(puede_eliminar_producto(self.admin, self.producto_de_juan))

    # ------------------------------------------------------------------
    # El administrador puede con productos ajenos
    # ------------------------------------------------------------------
    def test_staff_puede_abrir_la_edicion_de_un_producto_ajeno(self):
        self.client.force_login(self.admin)

        respuesta = self.client.get(
            reverse("producto_editar", args=[self.producto_de_juan.pk])
        )

        # Donde maria recibía 403, el admin entra sin problema.
        self.assertEqual(respuesta.status_code, 200)

    def test_staff_puede_editar_un_producto_ajeno(self):
        self.client.force_login(self.admin)

        respuesta = self.client.post(
            reverse("producto_editar", args=[self.producto_de_juan.pk]),
            {
                "nombre": "Portátil Lenovo",
                "descripcion": "Corregido por el admin",
                "precio": "849.99",
                "categoria": self.categoria.pk,
            },
        )

        self.assertEqual(respuesta.status_code, 302)
        self.producto_de_juan.refresh_from_db()
        self.assertEqual(self.producto_de_juan.nombre, "Portátil Lenovo")
        # El propietario no cambia: el admin solo ha editado.
        self.assertEqual(self.producto_de_juan.usuario, self.juan)

    def test_staff_puede_eliminar_un_producto_ajeno(self):
        self.client.force_login(self.admin)

        respuesta = self.client.post(
            reverse("producto_eliminar", args=[self.producto_de_juan.pk])
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assertFalse(
            Producto.objects.filter(pk=self.producto_de_juan.pk).exists()
        )

    def test_staff_ve_los_botones_en_producto_ajeno(self):
        self.client.force_login(self.admin)

        respuesta = self.client.get(
            reverse("producto_detalle", args=[self.producto_de_juan.pk])
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(
            respuesta, reverse("producto_editar", args=[self.producto_de_juan.pk])
        )

    # ------------------------------------------------------------------
    # El panel interno: solo staff
    # ------------------------------------------------------------------
    def test_panel_redirige_al_login_de_admin_si_no_hay_sesion(self):
        respuesta = self.client.get(reverse("panel_admin"))

        # staff_member_required manda a /admin/login/, no a nuestro login.
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn("/admin/login/", respuesta.headers["Location"])

    def test_panel_redirige_si_es_un_usuario_normal(self):
        self.client.force_login(self.maria)

        respuesta = self.client.get(reverse("panel_admin"))

        self.assertEqual(respuesta.status_code, 302)
        self.assertIn("/admin/login/", respuesta.headers["Location"])

    def test_panel_se_abre_para_el_staff(self):
        DatosDePrueba.producto(self.categoria, self.maria, nombre="Ratón")
        self.client.force_login(self.admin)

        respuesta = self.client.get(reverse("panel_admin"))

        self.assertEqual(respuesta.status_code, 200)
        self.assertTemplateUsed(respuesta, "administracion/panel.html")
        # Los dos contadores del panel.
        self.assertContains(respuesta, "Usuarios")
        self.assertContains(respuesta, "Productos")
        # Y la lista completa: se ven productos de maria y de juan.
        self.assertContains(respuesta, "Ratón")
        self.assertContains(respuesta, "Portátil")

    # ------------------------------------------------------------------
    # Interfaz: enlace al panel y badge de rol en el menú
    # ------------------------------------------------------------------
    def test_el_enlace_de_administracion_no_se_ve_como_normal(self):
        self.client.force_login(self.maria)

        respuesta = self.client.get(reverse("home"))

        self.assertEqual(respuesta.status_code, 200)
        self.assertNotContains(respuesta, reverse("panel_admin"))

    def test_el_enlace_de_administracion_se_ve_como_staff(self):
        self.client.force_login(self.admin)

        respuesta = self.client.get(reverse("home"))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, reverse("panel_admin"))
        self.assertContains(respuesta, "Administración")

    def test_badge_de_rol_en_el_menu(self):
        # Normal: badge gris.
        self.client.force_login(self.maria)
        respuesta = self.client.get(reverse("home"))
        self.assertContains(respuesta, "badge bg-secondary")
        self.assertNotContains(respuesta, "badge bg-danger")

        # Administrador: badge rojo con su rol.
        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse("home"))
        self.assertContains(respuesta, "badge bg-danger")
        self.assertContains(respuesta, "Administrador")
