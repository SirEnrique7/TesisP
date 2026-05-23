# ══════════════════════════════════════════════════════════════
# DECORATORS — Control de acceso por rol (RBAC)
# Reemplaza decorators.py existente
# ══════════════════════════════════════════════════════════════

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def _redirigir(request):
    """Destino de redirección según rol."""
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    return redirect('core:login')


def login_requerido(view_func):
    """Requiere sesión activa. Redirige al login si no."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('core:login')
        return view_func(request, *args, **kwargs)
    return wrapper


def solo_admin(view_func):
    """
    Solo Administradores activos.
    Los encargados ven un mensaje de acceso denegado.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('core:login')
        if not request.user.es_admin():
            messages.error(request, 'Acceso restringido: se requiere rol Administrador.')
            return redirect('core:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def solo_encargado(view_func):
    """Solo Encargados/Almacenistas."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('core:login')
        if not request.user.es_encargado():
            messages.error(request, 'Esta sección es exclusiva para encargados.')
            return redirect('core:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def bloquear_encargado(campos_sensibles=None):
    """
    Decorador de contexto: no bloquea la vista completa,
    sino que inyecta en el contexto si el usuario puede
    ver campos financieros sensibles (precios de compra,
    márgenes, saldos). Usado en templates con {% if puede_ver_financiero %}.

    Uso en vista:
        @login_requerido
        @bloquear_encargado()
        def mi_vista(request): ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            response = view_func(request, *args, **kwargs)
            # Inyectar flag en el contexto del template si es TemplateResponse
            if hasattr(response, 'context_data'):
                response.context_data['puede_ver_financiero'] = request.user.es_admin()
            return response
        return wrapper
    return decorator
