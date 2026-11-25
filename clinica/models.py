from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User


class Paciente(models.Model):
    usuario = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="perfil_paciente",
    )
    nombre = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    fecha_nacimiento = models.DateField()
    telefono = models.CharField(max_length=15)
    correo = models.EmailField(blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} {self.apellidos}"


class Medico(models.Model):
    ESPECIALIDADES = [
        ("GENERAL", "Medicina General"),
        ("PEDIATRIA", "Pediatría"),
        ("GINECOLOGIA", "Ginecología"),
        ("CARDIOLOGIA", "Cardiología"),
        ("DERMATOLOGIA", "Dermatología"),
    ]

    nombre = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    usuario = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="perfil_medico",
    )
    especialidad = models.CharField(max_length=20, choices=ESPECIALIDADES)
    telefono = models.CharField(max_length=15)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "médico"
        verbose_name_plural = "médicos"

    def __str__(self):
        return f"Dr(a). {self.nombre} {self.apellidos} - {self.get_especialidad_display()}"


class Horario(models.Model):
    DIAS = [
        (0, "Lunes"),
        (1, "Martes"),
        (2, "Miércoles"),
        (3, "Jueves"),
        (4, "Viernes"),
        (5, "Sábado"),
        (6, "Domingo"),
    ]

    medico = models.ForeignKey(Medico, on_delete=models.CASCADE, related_name="horarios")
    dia_semana = models.IntegerField(choices=DIAS)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    class Meta:
        verbose_name = "horario"
        verbose_name_plural = "horarios"
        ordering = ["medico", "dia_semana", "hora_inicio"]

    def __str__(self):
        return f"{self.medico.nombre} {self.medico.apellidos} - {self.get_dia_semana_display()} {self.hora_inicio:%H:%M}-{self.hora_fin:%H:%M}"

    
    def clean(self):
        if self.hora_inicio and self.hora_fin and self.hora_fin <= self.hora_inicio:
            raise ValidationError(
                {"hora_fin": "La hora de fin debe ser posterior a la hora de inicio."}
            )

class Cita(models.Model):
    ESTADOS = [
        ("PROGRAMADA", "Programada"),
        ("ATENDIDA", "Atendida"),
        ("CANCELADA", "Cancelada"),
    ]

    paciente = models.ForeignKey(Paciente, on_delete=models.PROTECT, related_name="citas")
    medico = models.ForeignKey(Medico, on_delete=models.PROTECT, related_name="citas")
    fecha = models.DateField()
    hora = models.TimeField()
    motivo = models.CharField(max_length=200)
    estado = models.CharField(max_length=15, choices=ESTADOS, default="PROGRAMADA")
    notas = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["fecha", "hora"]

    def __str__(self):
        return f"{self.fecha:%d/%m/%Y} {self.hora:%H:%M} - {self.paciente} con {self.medico}"