from django.db import models


class Paciente(models.Model):
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
    especialidad = models.CharField(max_length=20, choices=ESPECIALIDADES)
    telefono = models.CharField(max_length=15)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "médico"
        verbose_name_plural = "médicos"

    def __str__(self):
        return f"Dr(a). {self.nombre} {self.apellidos} - {self.get_especialidad_display()}"