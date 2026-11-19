from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("pacientes/", views.pacientes, name="pacientes"),
    path("pacientes/<int:paciente_id>/editar/", views.editar_paciente, name="editar_paciente"),
    path("medicos/", views.medicos, name="medicos"),
    path("medicos/<int:medico_id>/editar/", views.editar_medico, name="editar_medico"),
    path("horarios/nuevo/", views.agregar_horario, name="agregar_horario"),
    path("agenda/", views.agenda, name="agenda"),
    path("citas/<int:cita_id>/<str:estado>/", views.cambiar_estado, name="cambiar_estado"),
    path("login/", auth_views.LoginView.as_view(template_name="clinica/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
