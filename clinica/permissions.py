from functools import wraps

from django.core.exceptions import PermissionDenied


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


def roles_usuario(request):
    return {"es_administrador": es_administrador(request.user)}
