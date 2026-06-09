# ══════════════════════════════════════════════════════════════
# VIEWS — Módulo Compras (Versión Final Verificada y Certificada)
# ══════════════════════════════════════════════════════════════

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Sum
from django.forms import modelformset_factory
from decimal import Decimal
from typing import TYPE_CHECKING

from django.db.models import F as Fexpr
from .models import Compra, DetalleCompra
from .forms  import (
    CompraForm, DetalleCompraFormSet,
    AprobarCompraForm, RecepcionCompraForm,
    DetalleRecepcionForm, MarcarPagadoForm,
)
from core.models             import AuditoriaAccion, TasaCambio
from core.models_bimonetario import CuentaPorPagar
from core.decorators_core    import login_requerido, solo_admin
from inventario.models       import MovimientoInventario

# Declaración estática para que Pylance comprenda las relaciones inversas del ORM
if TYPE_CHECKING:
    from django.db.models.manager import RelatedManager
    class CompraConDetalles(Compra):
        detalles: RelatedManager[DetalleCompra]


# ─────────────────────────────────────────────
# LISTA DE COMPRAS
# ─────────────────────────────────────────────
@login_requerido
def lista_compras(request):
    estado = request.GET.get('estado', '')
    q      = request.GET.get('q', '')

    qs = Compra.objects.select_related('proveedor', 'creada_por', 'aprobada_por')

    if not request.user.es_admin():
        qs = qs.filter(creada_por=request.user)

    if estado:
        qs = qs.filter(estado=estado)
    if q:
        qs = qs.filter(
            Q(numero_referencia__icontains=q) |
            Q(proveedor__nombre__icontains=q)
        )

    qs = qs.order_by('-fecha_creacion')

    pendientes = Compra.objects.filter(estado='pendiente').count() if request.user.es_admin() else 0

    return render(request, 'compras/lista_compras.html', {
        'compras':    qs,
        'estados': Compra.ESTADO_CHOICES,
        'estado':     estado,
        'q':          q,
        'pendientes': pendientes,
    })


# ─────────────────────────────────────────────
# CREAR ORDEN (Sincronizado con HTML Dinámico)
# ─────────────────────────────────────────────
@login_requerido
def crear_compra(request):
    from inventario.models import Producto
    sugerencias = []
    proveedor_id = request.GET.get('proveedor') or request.POST.get('proveedor')
    
    if proveedor_id:
        sugerencias = Producto.objects.filter(
            proveedor_id=proveedor_id, activo=True
        ).filter(
            Q(stock_actual__lte=Fexpr('stock_minimo')) | Q(en_tendencia=True)
        ).order_by('stock_actual')[:10]

    if request.method == 'POST':
        form    = CompraForm(request.POST)
        formset = DetalleCompraFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    compra             = form.save(commit=False)
                    compra.creada_por  = request.user
                    compra.estado      = 'pendiente'
                    compra.save()

                    # Guardado controlado para forzar cálculos de subtotales por fila
                    detalles_instancias = formset.save(commit=False)
                    for detalle in detalles_instancias:
                        detalle.compra = compra
                        detalle.save()
                    
                    formset.save_m2m()

                    # Cálculo matemático global sobre los subtotales reales asentados
                    compra.calcular_total()

                AuditoriaAccion.registrar(
                    usuario=request.user, accion='crear_compra',
                    descripcion=f'Orden {compra.numero_referencia} creada — {compra.proveedor}',
                    request=request, objeto_tipo='Compra', objeto_id=compra.pk,
                )
                messages.success(
                    request,
                    f'Orden {compra.numero_referencia} creada y enviada al administrador para aprobación.'
                )
                return redirect('compras:detalle_compra', pk=compra.pk)
            except Exception as e:
                messages.error(request, f'Error interno al procesar la orden: {str(e)}')
        else:
            messages.error(request, 'Revisa los errores en el formulario de productos.')
    else:
        form    = CompraForm()
        formset = DetalleCompraFormSet(queryset=DetalleCompra.objects.none())

    return render(request, 'compras/form_compra.html', {
        'form':        form,
        'formset':     formset,
        'titulo':      'Nueva orden de compra',
        'sugerencias': sugerencias,
    })


# ─────────────────────────────────────────────
# DETALLE DE COMPRA (Tipado Asistido)
# ─────────────────────────────────────────────
@login_requerido
def detalle_compra(request, pk):
    # El casteo mediante comentario le indica a VS Code la estructura extendida
    compra: 'CompraConDetalles' = get_object_or_404(Compra, pk=pk) # type: ignore

    if not request.user.es_admin() and compra.creada_por != request.user:
        messages.error(request, 'No tienes acceso a esta orden.')
        return redirect('compras:lista_compras')

    detalles = compra.detalles.select_related('producto').all()
    cuenta   = getattr(compra, 'cuenta_por_pagar', None)

    return render(request, 'compras/detalle_compra.html', {
        'compra':   compra,
        'detalles': detalles,
        'cuenta':   cuenta,
    })


# ─────────────────────────────────────────────
# APROBAR / RECHAZAR (Tipado Asistido)
# ─────────────────────────────────────────────
@solo_admin
def aprobar_compra(request, pk):
    compra: 'CompraConDetalles' = get_object_or_404(Compra, pk=pk, estado='pendiente') # type: ignore

    if request.method == 'POST':
        form = AprobarCompraForm(request.POST)
        if form.is_valid():
            decision = form.cleaned_data['decision']
            motivo   = form.cleaned_data['motivo_rechazo']

            with transaction.atomic():
                compra.estado            = decision
                compra.aprobada_por      = request.user
                compra.fecha_aprobacion  = timezone.now()
                if motivo:
                    compra.motivo_rechazo = motivo
                compra.save()

            accion = 'aprobar_compra' if decision == 'aprobada' else 'rechazar_compra'
            AuditoriaAccion.registrar(
                usuario=request.user, accion=accion,
                descripcion=f'Orden {compra.numero_referencia} {decision}. {motivo}',
                request=request, objeto_tipo='Compra', objeto_id=compra.pk,
            )

            if decision == 'aprobada':
                messages.success(
                    request,
                    f'Orden {compra.numero_referencia} aprobada. El encargado puede ver que está "En camino".'
                )
            else:
                messages.warning(request, f'Orden {compra.numero_referencia} rechazada.')

            return redirect('compras:detalle_compra', pk=compra.pk)
    else:
        form = AprobarCompraForm()

    return render(request, 'compras/aprobar_compra.html', {
        'compra':   compra,
        'detalles': compra.detalles.select_related('producto').all(),
        'form':     form,
    })


# ─────────────────────────────────────────────
# REGISTRAR RECEPCIÓN (Flujo Seguro Completo)
# ─────────────────────────────────────────────
@solo_admin
def recibir_compra(request, pk):
    compra: 'CompraConDetalles' = get_object_or_404(Compra, pk=pk, estado='aprobada') # type: ignore
    detalles = compra.detalles.select_related('producto').all()

    RecepcionFormSet = modelformset_factory(
        DetalleCompra,
        form=DetalleRecepcionForm,
        extra=0,
    )

    if request.method == 'POST':
        form_recepcion = RecepcionCompraForm(request.POST, instance=compra)
        formset        = RecepcionFormSet(request.POST, queryset=detalles)

        if form_recepcion.is_valid() and formset.is_valid():
            with transaction.atomic():
                formset.save()
                recepcion = form_recepcion.save(commit=False)

                # Ciclo limpio y nativo reconocido perfectamente por Pylance
                for detalle in compra.detalles.select_related('producto').all():
                    if detalle.cantidad_recibida > 0:
                        prod = detalle.producto
                        prod.stock_actual += detalle.cantidad_recibida
                        prod.save(update_fields=['stock_actual'])

                        MovimientoInventario.objects.create(
                            producto=prod,
                            tipo='entrada',
                            cantidad=detalle.cantidad_recibida,
                            motivo=f'Recepción {compra.numero_referencia} — {compra.proveedor.nombre}',
                            usuario=request.user,
                        )

                compra.estado          = 'recibida'
                compra.fecha_recepcion = recepcion.fecha_recepcion or timezone.now()
                compra.modalidad_pago  = recepcion.modalidad_pago
                compra.fecha_vencimiento = recepcion.fecha_vencimiento

                tasa_obj = TasaCambio.tasa_vigente()
                tasa     = tasa_obj.tasa_bs_usd if tasa_obj else None

                compra.calcular_total()  # Recalcula totales basados en lo físico recibido

                if recepcion.modalidad_pago == 'contado':
                    compra.pagado = True
                    compra.save()
                else:
                    compra.pagado = False
                    compra.save()

                    cpp = CuentaPorPagar(
                        proveedor        = compra.proveedor,
                        compra           = compra,
                        saldo_restante   = compra.total,
                        fecha_vencimiento = compra.fecha_vencimiento,
                        registrada_por   = request.user,
                    )
                    cpp.fijar_conversion(compra.total, tasa)
                    cpp.save()

            AuditoriaAccion.registrar(
                usuario=request.user, accion='recibir_compra',
                descripcion=f'Recepción registrada: {compra.numero_referencia}. Pago: {compra.get_modalidad_pago_display()}. Ref: {compra.referencia_documento}',
                request=request, objeto_tipo='Compra', objeto_id=compra.pk,
            )

            messages.success(
                request,
                f'Recepción registrada. Stock actualizado. ' + 
                ('Cuenta por pagar generada.' if compra.modalidad_pago == 'credito' else 'Pago registrado al contado.')
            )
            return redirect('compras:detalle_compra', pk=compra.pk)
        else:
            messages.error(request, 'Revisa los errores antes de continuar.')
    else:
        form_recepcion = RecepcionCompraForm(instance=compra)
        formset        = RecepcionFormSet(queryset=detalles)

    return render(request, 'compras/recibir_compra.html', {
        'compra':          compra,
        'detalles':        detalles,
        'form_recepcion':  form_recepcion,
        'formset':         formset,
        'formset_detalle': zip(formset, detalles),
    })


# ─────────────────────────────────────────────
# CANCELAR COMPRA (Órdenes Inactivas)
# ─────────────────────────────────────────────
@login_requerido
def cancelar_compra(request, pk):
    compra = get_object_or_404(Compra, pk=pk)

    if compra.estado not in ['pendiente']:
        messages.error(request, 'Solo se pueden cancelar órdenes pendientes.')
        return redirect('compras:detalle_compra', pk=pk)

    if not request.user.es_admin() and compra.creada_por != request.user:
        messages.error(request, 'No tienes permiso para cancelar esta orden.')
        return redirect('compras:lista_compras')

    if request.method == 'POST':
        compra.estado = 'cancelada'
        compra.save()
        
        AuditoriaAccion.registrar(
            usuario=request.user, accion='cancelar_compra',
            descripcion=f'Orden {compra.numero_referencia} cancelada.',
            request=request, objeto_tipo='Compra', objeto_id=compra.pk,
        )
        messages.warning(request, f'Orden {compra.numero_referencia} cancelada.')
        return redirect('compras:lista_compras')

    return render(request, 'compras/cancelar_compra.html', {'compra': compra})