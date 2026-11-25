from functools import wraps

from django.core.exceptions import PermissionDenied

from .forms import roles_disponibles


ADMINISTRADOR = "Administrador"


def es_administrador(user):
    return user.is_authenticated and (
        user.is_superuser or user.groups.filter(name=ADMINISTRADOR).exists()
    )


def administrador_requerido(view_func):
    @wraps(view_func)
    def comprobar_permiso(request, *args, **kwargs):
        if not es_administrador(request.user):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return comprobar_permiso


def rol_actual(request):
    roles = roles_disponibles(request.user)
    rol_sesion = request.session.get("rol_activo")
    if rol_sesion in roles:
        return rol_sesion
    return roles[0] if roles else ""


def roles_requeridos(*roles_permitidos):
    def decorar(view_func):
        @wraps(view_func)
        def comprobar_permiso(request, *args, **kwargs):
            if rol_actual(request) not in roles_permitidos:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return comprobar_permiso

    return decorar


def roles_usuario(request):
    rol = rol_actual(request)
    nombres = {
        "paciente": "Paciente",
        "medico": "Médico",
        "recepcionista": "Recepcionista",
        "administrador": "Administrador",
    }
    return {
        "es_administrador": rol == "administrador",
        "es_paciente": rol == "paciente",
        "es_medico": rol == "medico",
        "es_recepcionista": rol == "recepcionista",
        "rol_nombre": nombres.get(rol, "Usuario"),
    }
