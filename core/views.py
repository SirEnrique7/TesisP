# ══════════════════════════════════════════════════════════════
# VIEWS — Módulo Core
# ══════════════════════════════════════════════════════════════

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings

from .models import Usuario, TasaCambio, AuditoriaAccion
from .forms import (
    LoginForm, UsuarioCrearForm, UsuarioEditarForm,
    RecuperarPasswordForm, NuevaPasswordForm
)
from .decorators_core import login_requerido, solo_admin
from .bcv_scraper import actualizar_tasa_hoy


# ─────────────────────────────────────────────
# AUTH: Login / Logout
# ─────────────────────────────────────────────

def vista_login(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    form = LoginForm(request, data=request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            usuario = form.get_user()
            login(request, usuario)

            AuditoriaAccion.registrar(
                usuario=usuario, accion='login',
                descripcion=f'Inicio de sesión exitoso.',
                request=request,
            )

            # Actualizar tasa BCV al primer login del día (en segundo plano)
            try:
                actualizar_tasa_hoy()
            except Exception:
                pass  # No bloquear el login si el scraper falla

            return redirect('core:dashboard')
        else:
            # Registrar intento fallido
            username_intent = request.POST.get('username', '')
            AuditoriaAccion.registrar(
                usuario=None, accion='login_fallido',
                descripcion=f'Intento fallido para usuario: "{username_intent}"',
                request=request,
            )
            messages.error(request, 'Usuario o contraseña incorrectos.')

    return render(request, 'core/login.html', {'form': form})


@login_requerido
def vista_logout(request):
    AuditoriaAccion.registrar(
        usuario=request.user, accion='logout',
        descripcion='Cierre de sesión.',
        request=request,
    )
    logout(request)
    return redirect('core:login')


# ─────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────

@login_requerido
def dashboard(request):
    from inventario.models import Producto
    from compras.models import Compra
    from ventas.models import Venta, CuentaPorCobrar

    tasa_hoy = TasaCambio.tasa_vigente()

    # Stats comunes
    total_productos    = Producto.objects.filter(activo=True).count()
    productos_bajo     = [p for p in Producto.objects.filter(activo=True) if p.stock_bajo]
    compras_pendientes = Compra.objects.filter(estado='pendiente').count()

    context = {
        'tasa_hoy':            tasa_hoy,
        'total_productos':     total_productos,
        'productos_bajo':      productos_bajo[:5],
        'compras_pendientes':  compras_pendientes,
        'puede_ver_financiero': request.user.es_admin(),
    }

    # Stats exclusivas del admin
    if request.user.es_admin():
        from ventas.models import CuentaPorCobrar, CuentaPorPagar
        from django.db.models import Sum
        from datetime import date

        context['cuentas_por_cobrar'] = CuentaPorCobrar.objects.filter(
            estado='pendiente'
        ).aggregate(total=Sum('saldo_restante'))['total'] or 0

        context['cuentas_por_pagar'] = CuentaPorPagar.objects.filter(
            estado='pendiente'
        ).aggregate(total=Sum('saldo_restante'))['total'] or 0

        context['creditos_vencidos'] = CuentaPorCobrar.objects.filter(
            estado='pendiente',
            fecha_estimada_pago__lt=date.today()
        ).count()

        context['ventas_hoy'] = Venta.objects.filter(
            fecha=date.today(), estado__in=['procesada', 'a_credito']
        ).aggregate(total=Sum('total_bs'))['total'] or 0

    return render(request, 'core/dashboard.html', context)


# ─────────────────────────────────────────────
# GESTIÓN DE USUARIOS (solo Admin)
# ─────────────────────────────────────────────

@solo_admin
def lista_usuarios(request):
    usuarios = Usuario.objects.all().order_by('is_active', 'last_name')
    return render(request, 'core/lista_usuarios.html', {'usuarios': usuarios})


@solo_admin
def crear_usuario(request):
    if request.method == 'POST':
        form = UsuarioCrearForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            AuditoriaAccion.registrar(
                usuario=request.user, accion='alta_usuario',
                descripcion=f'Usuario creado: {usuario.get_nombre_completo()} ({usuario.cedula})',
                request=request, objeto_tipo='Usuario', objeto_id=usuario.pk,
            )
            messages.success(request, f'Usuario "{usuario.get_nombre_completo()}" creado correctamente.')
            return redirect('core:lista_usuarios')
    else:
        form = UsuarioCrearForm()

    return render(request, 'core/form_usuario.html', {
        'form':   form,
        'titulo': 'Nuevo usuario',
        'accion': 'Crear',
    })


@solo_admin
def editar_usuario(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)

    if request.method == 'POST':
        form = UsuarioEditarForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            AuditoriaAccion.registrar(
                usuario=request.user, accion='edicion_usuario',
                descripcion=f'Usuario editado: {usuario.get_nombre_completo()}',
                request=request, objeto_tipo='Usuario', objeto_id=usuario.pk,
            )
            messages.success(request, 'Usuario actualizado correctamente.')
            return redirect('core:lista_usuarios')
    else:
        form = UsuarioEditarForm(instance=usuario)

    return render(request, 'core/form_usuario.html', {
        'form':    form,
        'titulo':  f'Editar: {usuario.get_nombre_completo()}',
        'accion':  'Guardar cambios',
        'usuario': usuario,
    })


@solo_admin
def dar_de_baja(request, pk):
    """Baja lógica: is_active = False. Nunca DELETE."""
    usuario = get_object_or_404(Usuario, pk=pk)

    # No permitir darse de baja a sí mismo
    if usuario == request.user:
        messages.error(request, 'No puedes darte de baja a ti mismo.')
        return redirect('core:lista_usuarios')

    if request.method == 'POST':
        usuario.dar_de_baja(ejecutado_por=request.user)
        AuditoriaAccion.registrar(
            usuario=request.user, accion='baja_usuario',
            descripcion=f'Baja lógica ejecutada sobre: {usuario.get_nombre_completo()} ({usuario.cedula})',
            request=request, objeto_tipo='Usuario', objeto_id=usuario.pk,
        )
        messages.warning(request, f'Usuario "{usuario.get_nombre_completo()}" dado de baja. Sus registros históricos se mantienen intactos.')
        return redirect('core:lista_usuarios')

    return render(request, 'core/confirmar_baja.html', {'usuario': usuario})


@solo_admin
def reactivar_usuario(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk, is_active=False)
    if request.method == 'POST':
        usuario.reactivar(ejecutado_por=request.user)
        messages.success(request, f'Usuario "{usuario.get_nombre_completo()}" reactivado.')
        return redirect('core:lista_usuarios')
    return render(request, 'core/confirmar_reactivar.html', {'usuario': usuario})


# ─────────────────────────────────────────────
# RECUPERACIÓN DE CONTRASEÑA
# ─────────────────────────────────────────────

def recuperar_password(request):
    if request.method == 'POST':
        form = RecuperarPasswordForm(request.POST)
        if form.is_valid():
            email   = form.cleaned_data['email']
            usuario = Usuario.objects.get(email=email, is_active=True)
            uid     = urlsafe_base64_encode(force_bytes(usuario.pk))
            token   = default_token_generator.make_token(usuario)

            enlace = request.build_absolute_uri(
                f'/auth/reset/{uid}/{token}/'
            )

            send_mail(
                subject='Recuperación de contraseña — Inversiones Ramón',
                message=(
                    f'Hola {usuario.get_nombre_completo()},\n\n'
                    f'Haz clic en el siguiente enlace para restablecer tu contraseña '
                    f'(válido por 15 minutos):\n\n{enlace}\n\n'
                    f'Si no solicitaste esto, ignora este mensaje.'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            messages.success(request, 'Se envió un enlace de recuperación a tu correo.')
            return redirect('core:login')
    else:
        form = RecuperarPasswordForm()

    return render(request, 'core/recuperar_password.html', {'form': form})


def reset_password(request, uidb64, token):
    try:
        uid     = force_str(urlsafe_base64_decode(uidb64))
        usuario = Usuario.objects.get(pk=uid)
    except (TypeError, ValueError, Usuario.DoesNotExist):
        usuario = None

    # Validar token (expira en 15 min via settings.PASSWORD_RESET_TIMEOUT)
    if usuario is None or not default_token_generator.check_token(usuario, token):
        messages.error(request, 'El enlace es inválido o ha expirado.')
        return redirect('core:recuperar_password')

    if request.method == 'POST':
        form = NuevaPasswordForm(usuario, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Contraseña actualizada correctamente. Inicia sesión.')
            return redirect('core:login')
    else:
        form = NuevaPasswordForm(usuario)

    return render(request, 'core/reset_password.html', {'form': form})


# ─────────────────────────────────────────────
# AUDITORÍA (solo Admin)
# ─────────────────────────────────────────────

@solo_admin
def log_auditoria(request):
    logs = AuditoriaAccion.objects.select_related('usuario').all()[:200]
    return render(request, 'core/auditoria.html', {'logs': logs})


# ─────────────────────────────────────────────
# TASA BCV (solo Admin)
# ─────────────────────────────────────────────

@solo_admin
def historial_tasa(request):
    tasas = TasaCambio.objects.all()[:30]
    return render(request, 'core/historial_tasa.html', {'tasas': tasas})
