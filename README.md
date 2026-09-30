# Tienda Django | UF2406ED01

Aplicación web académica para gestionar un catálogo de productos y categorías. El catálogo puede consultarse sin iniciar sesión; las operaciones de gestión requieren una cuenta.

## Funciones actuales

- Registro de usuarios e inicio y cierre de sesión.
- Listado y detalle público de productos.
- Creación, edición y eliminación de productos para usuarios autenticados.
- Propiedad de los productos: cada uno queda asociado a su creador y solo él puede editarlo o eliminarlo.
- Página «Mis productos» con el listado personal de cada cuenta.
- Gestión de categorías para usuarios autenticados.
- Recuperación de contraseña mediante las vistas integradas de Django.
- Panel de administración de Django con búsqueda y filtros.
- Interfaz adaptable con Bootstrap 5, navegación responsive y mensajes de estado.
- Páginas de error personalizadas para 403 y 404.

## Tecnologías

- Python 3.12 y Django 6.1.1 comprobados en el entorno local.
- SQLite (`db.sqlite3`) como base de datos de desarrollo.
- Plantillas Django y Bootstrap 5 cargado desde CDN; no se necesita un proceso de compilación frontend.

El proyecto aún no cuenta con un manifiesto de dependencias (`requirements.txt` o `pyproject.toml`).

## Estructura

```text
.
├── manage.py
├── db.sqlite3
├── tienda/              # Configuración y rutas del proyecto
├── productos/           # Modelos, formularios, vistas y rutas de la aplicación
├── templates/           # Plantillas HTML
└── UF2406ED01_*.txt     # Enunciados de la práctica
```

## Instalación y ejecución

Requiere Python y `pip`. Desde la raíz del proyecto, crea un entorno virtual e instala Django.

**Windows (PowerShell):**

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install "Django==6.1.1"
```

**Linux o macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install "Django==6.1.1"
```

Aplica las migraciones e inicia el servidor:

```bash
python manage.py migrate
python manage.py runserver
```

Abre <http://127.0.0.1:8000/>. Para crear una cuenta del panel de administración:

```bash
python manage.py createsuperuser
```

El panel está disponible en <http://127.0.0.1:8000/admin/>. Detén el servidor con `Ctrl+C`.

## Modelo de datos

Una `Categoria` puede contener varios `Producto`; cada producto pertenece a una categoría. Un `Usuario` puede tener varios `Producto`; cada producto tiene un único propietario. Los productos guardan nombre, descripción, precio, categoría, propietario y fecha de creación. Al eliminar una categoría, Django elimina también sus productos asociados; al eliminar una cuenta, sus productos.

El propietario no se elige en el formulario: lo asigna la vista con `request.user` mediante `form.save(commit=False)`, y las vistas de edición y eliminación filtran con `usuario=request.user`, de modo que cualquier intento de entrar por URL directa a un producto ajeno responde 404.

## Recuperación de contraseña

En desarrollo, Django usa el backend de correo de consola: el enlace de recuperación aparece en la terminal del servidor y no se envía un correo real.

## Comprobaciones

```bash
python manage.py check
python manage.py test
```

La suite cubre las páginas públicas, la protección de las vistas privadas, el CRUD de categorías y productos, el registro, el flujo completo de recuperación de contraseña y el control de propiedad sobre los productos (propietario asignado automáticamente, «Mis productos» y bloqueo de edición y borrado ajenos). Ejecuta `python manage.py test` para verificarla.
