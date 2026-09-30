"""
Formularios de la aplicación.

Un formulario en Django se encarga de dos cosas a la vez:
pintar el HTML en pantalla y validar lo que escribe el usuario
antes de guardarlo en la base de datos.

Aquí tenemos tres:

- RegistroForm:  crear cuenta (usuario, email y contraseña dos veces).
- CategoriaForm: alta y edición de categorías.
- ProductoForm:  alta y edición de productos.

Además, todos comparten BootstrapFormMixin, que es lo que les pinta
las clases de Bootstrap 5 sin tener que escribirlas a mano campo a campo.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Categoria, Producto


class BootstrapFormMixin:
    """Pone las clases de Bootstrap 5 en todos los campos del formulario.

    Django genera cada campo con su widget, y un widget acepta atributos
    HTML extra en attrs. Aquí simplemente recorremos los campos y le
    añadimos la clase que corresponda: form-control para lo que escribe
    el usuario, form-check-input para las casillas de verificación.
    """

    def aplicar_bootstrap(self):

        for field in self.fields.values():

            if isinstance(
                field.widget,
                forms.CheckboxInput
            ):

                # Casillas: Bootstrap espera form-check-input.
                field.widget.attrs[
                    "class"
                ] = "form-check-input"

            else:

                # Cajas de texto, desplegables, etc.: form-control.
                field.widget.attrs[
                    "class"
                ] = "form-control"


class RegistroForm(
    BootstrapFormMixin,
    UserCreationForm
):
    # Heredamos de UserCreationForm para no reescribir lo que Django
    # ya hace bien: comprobar que las dos contraseñas coinciden,
    # que cumple los validadores de seguridad, etc.
    # Lo único que añadimos es el email, y lo marcamos como obligatorio.
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password1",
            "password2",
        ]

    def __init__(
        self,
        *args,
        **kwargs
    ):

        # Al construir el formulario llamamos primero al inicializador
        # original (para que Django monte los campos) y después le
        # aplicamos las clases de Bootstrap.
        super().__init__(
            *args,
            **kwargs
        )

        self.aplicar_bootstrap()

    def clean_email(self):
        # Este método se ejecuta solo cuando el usuario pulsa "Registrarse".
        # Si ya hay alguien con ese correo, no dejamos continuar:
        # así evitamos cuentas duplicadas con el mismo email.
        # email__iexact compara sin distinguir mayúsculas de minúsculas,
        # así "JuAN@email.com" y "juan@email.com" cuentan como el mismo.
        email = self.cleaned_data.get("email")

        if User.objects.filter(
            email__iexact=email
        ).exists():
            raise forms.ValidationError(
                "Ya existe un usuario con este email."
            )

        return email


class CategoriaForm(
    BootstrapFormMixin,
    forms.ModelForm
):

    class Meta:
        model = Categoria
        # No incluimos fecha_creacion: esa fecha la pone Django sola.
        fields = [
            "nombre",
            "descripcion",
        ]

        # La descripción necesita más altura que un input de una línea,
        # así que le damos 4 filas al textarea.
        widgets = {

            "descripcion":
                forms.Textarea(
                    attrs={
                        "rows": 4
                    }
                )

        }

    def __init__(
        self,
        *args,
        **kwargs
    ):

        super().__init__(
            *args,
            **kwargs
        )

        self.aplicar_bootstrap()


class ProductoForm(
    BootstrapFormMixin,
    forms.ModelForm
):

    class Meta:
        model = Producto
        # Ojo: "usuario" NO está en la lista, y es intencionado.
        # El propietario no se elige en el formulario porque nadie
        # debería poder crear productos ajenos; lo asigna la vista
        # con request.user usando form.save(commit=False).
        fields = [
            "nombre",
            "descripcion",
            "precio",
            "categoria",
        ]

        # Mismo motivo que en CategoriaForm: la descripción es un
        # párrafo y un input de una línea se queda muy corto.
        widgets = {

            "descripcion":
                forms.Textarea(
                    attrs={
                        "rows": 4
                    }
                )

        }

    def __init__(
        self,
        *args,
        **kwargs
    ):

        super().__init__(
            *args,
            **kwargs
        )

        self.aplicar_bootstrap()
