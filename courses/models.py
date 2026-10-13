from django.core.validators import MinValueValidator
from django.db import models


class CourseModality(models.TextChoices):
    PRESENCIAL = "presencial", "Presencial"
    ONLINE = "online", "Online"
    HYBRID = "hybrid", "Híbrida"


class Course(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name="Título",
    )
    description = models.TextField(
        blank=True,
        verbose_name="Descripción",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Activo",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Última actualización",
    )

    class Meta:
        verbose_name = "Curso"
        verbose_name_plural = "Cursos"
        ordering = ["title"]
        indexes = [
            models.Index(fields=["title"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.title


class Convocatoria(models.Model):
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="convocatorias",
        verbose_name="Curso",
    )
    name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Nombre",
        help_text="Ej: Verano 2026, Grupo A, Mañanas",
    )
    start_date = models.DateField()
    enrollment_deadline = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha límite de inscripción",
    )
    schedule = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Horario",
        help_text="Ej: L-X-V 18:00-20:00",
    )
    modality = models.CharField(
        max_length=20,
        choices=CourseModality.choices,
        default=CourseModality.PRESENCIAL,
        verbose_name="Modalidad",
    )
    location = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Ubicación",
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Precio",
    )
    deposit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Señal / Reserva",
        help_text="Cantidad a pagar para reservar plaza",
    )
    total_places = models.PositiveIntegerField(
        default=0,
        verbose_name="Plazas totales",
    )
    # El PDF usa reserved_places pero omite su declaración; se deduce el
    # contador de plazas con el mismo tipo y valor inicial de enrolled_places.
    reserved_places = models.PositiveIntegerField(
        default=0,
        verbose_name="Plazas reservadas",
    )
    enrolled_places = models.PositiveIntegerField(
        default=0,
        verbose_name="Plazas matriculadas",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Activa",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Última actualización",
    )

    class Meta:
        verbose_name = "Convocatoria"
        verbose_name_plural = "Convocatorias"
        ordering = ["start_date"]
        indexes = [
            models.Index(fields=["start_date"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["course"]),
        ]

    def __str__(self):
        label = self.name or f"{self.start_date}"
        return f"{self.course.title} — {label}"

    @property
    def available_places(self):
        used = self.reserved_places + self.enrolled_places
        return max(self.total_places - used, 0)

    @property
    def is_full(self):
        return self.available_places == 0

    @property
    def is_open(self):
        from django.utils import timezone

        if not self.is_active or self.is_full:
            return False
        if (
            self.enrollment_deadline
            and timezone.localdate() > self.enrollment_deadline
        ):
            return False
        return True
