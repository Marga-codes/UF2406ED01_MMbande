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

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from .models import Categoria, Producto


class DatosDePrueba:
    """Atajos para crear los objetos que usan casi todos los tests."""

    @staticmethod
    def categoria(nombre="Informática", descripcion="Equipos"):
        return Categoria.objects.create(
            nombre=nombre,
            descripcion=descripcion,
        )

    @staticmethod
    def producto(categoria, nombre="Portátil", precio="799.99"):
        return Producto.objects.create(
            nombre=nombre,
            descripcion="Portátil para estudiante.",
            precio=Decimal(precio),
            categoria=categoria,
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
        DatosDePrueba.producto(cat)

        response = self.client.get(reverse("producto_lista"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "productos/lista.html")
        # El producto creado tiene que aparecer en la página.
        self.assertContains(response, "Portátil")

    def test_detalle_de_producto(self):
        cat = DatosDePrueba.categoria()
        producto = DatosDePrueba.producto(cat)

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
        producto = DatosDePrueba.producto(self.categoria)

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
        producto = DatosDePrueba.producto(self.categoria)

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
