from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.db.models.functions import Coalesce
from decimal import Decimal
from datetime import date

from core.models_bimonetario import (
    CuentaPorPagar, CuentaPorCobrar, Cliente,
    AbonoCuentaPagar, AbonoCuentaCobrar
)
from .models import TasaCambio, AuditoriaAccion
from .forms_bimonetario import AbonoProveedorForm, PagoClienteForm, ClienteForm
from .decorators_core import solo_admin, login_requerido


# ══════════════════════════════════════════════
# CUENTAS POR PAGAR (proveedores)
# ══════════════════════════════════════════════

@solo_admin
def lista_cuentas_pagar(request):
    estado = request.GET.get('estado', 'pendiente')

    cuentas = CuentaPorPagar.objects.select_related(
        'proveedor', 'compra'
    ).order_by('fecha_vencimiento')

    if estado != 'todas':
        cuentas = cuentas.filter(estado=estado)

    resumen = CuentaPorPagar.objects.filter(
        estado__in=['pendiente', 'abonada']
    ).aggregate(
        total_bs=Coalesce(Sum('saldo_restante'), Decimal('0.00')),
        total_usd=Coalesce(Sum('monto_usd'), Decimal('0.00')),
        cantidad=Count('id'),
        vencidas=Count('id', filter=Q(fecha_vencimiento__lt=date.today()))
    )

    tasa_hoy = TasaCambio.tasa_vigente()

    return render(request, 'core/cuentas_pagar/lista.html', {
        'cuentas': cuentas,
        'estado': estado,
        'resumen': resumen,
        'tasa_hoy': tasa_hoy,
    })


@solo_admin
def detalle_cuenta_pagar(request, pk):
    cuenta = get_object_or_404(CuentaPorPagar, pk=pk)
    abonos = cuenta.abonos.select_related('registrado_por').all()
    
    tasa_hoy = TasaCambio.tasa_vigente()
    tasa_valor = tasa_hoy.tasa_bs_usd if tasa_hoy else None
    form = AbonoProveedorForm(cuenta=cuenta, initial={'tasa_bcv': tasa_valor})

    return render(request, 'core/cuentas_pagar/detalle.html', {
        'cuenta': cuenta,
        'abonos': abonos,
        'form': form,
    })


@solo_admin
def registrar_abono_proveedor(request, pk):
    with transaction.atomic():
        cuenta = get_object_or_404(CuentaPorPagar.objects.select_for_update(), pk=pk)

        if cuenta.estado == 'saldada':
            messages.info(request, 'Esta cuenta ya está saldada.')
            return redirect('core:detalle_cuenta_pagar', pk=pk)

        if request.method == 'POST':
            form = AbonoProveedorForm(request.POST, cuenta=cuenta)
            if form.is_valid():
                try:
                    cuenta.registrar_abono(
                        monto_abono=form.cleaned_data['monto_bs'],
                        tasa_bcv=form.cleaned_data['tasa_bcv'],
                        referencia=form.cleaned_data['referencia'],
                        usuario=request.user,
                    )
                    AuditoriaAccion.registrar(
                        usuario=request.user, accion='pago_proveedor',
                        descripcion=f'Abono Bs. {form.cleaned_data["monto_bs"]} a {cuenta.proveedor} — Ref: {form.cleaned_data["referencia"]}',
                        request=request, objeto_tipo='CuentaPorPagar', objeto_id=cuenta.pk,
                    )
                    messages.success(request, 'Abono registrado correctamente.')
                except ValueError as e:
                    messages.error(request, str(e))
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')
    return redirect('core:detalle_cuenta_pagar', pk=pk)


# ══════════════════════════════════════════════
# CUENTAS POR COBRAR (clientes)
# ══════════════════════════════════════════════

@solo_admin
def lista_cuentas_cobrar(request):
    estado = request.GET.get('estado', 'pendiente')

    cuentas = CuentaPorCobrar.objects.select_related(
        'cliente', 'venta'
    ).order_by('fecha_estimada_pago')

    if estado != 'todas':
        cuentas = cuentas.filter(estado=estado)

    resumen = CuentaPorCobrar.objects.filter(
        estado__in=['pendiente', 'abonada']
    ).aggregate(
        total_bs=Coalesce(Sum('saldo_restante'), Decimal('0.00')),
        total_usd=Coalesce(Sum('monto_usd'), Decimal('0.00')),
        cantidad=Count('id'),
        vencidas=Count('id', filter=Q(fecha_estimada_pago__lt=date.today()))
    )

    tasa_hoy = TasaCambio.tasa_vigente()

    return render(request, 'core/cuentas_cobrar/lista.html', {
        'cuentas': cuentas,
        'estado': estado,
        'resumen': resumen,
        'tasa_hoy': tasa_hoy,
    })


@solo_admin
def detalle_cuenta_cobrar(request, pk):
    cuenta = get_object_or_404(CuentaPorCobrar, pk=pk)
    abonos = cuenta.abonos.select_related('registrado_por').all()
    tasa_hoy = TasaCambio.tasa_vigente()
    tasa_valor = tasa_hoy.tasa_bs_usd if tasa_hoy else None
    form = PagoClienteForm(cuenta=cuenta, initial={'tasa_bcv': tasa_valor})

    return render(request, 'core/cuentas_cobrar/detalle.html', {
        'cuenta': cuenta,
        'abonos': abonos,
        'form': form,
    })


@solo_admin
def registrar_pago_cliente(request, pk):
    with transaction.atomic():
        cuenta = get_object_or_404(CuentaPorCobrar.objects.select_for_update(), pk=pk)

        if cuenta.estado == 'saldada':
            messages.info(request, 'Esta cuenta ya está saldada.')
            return redirect('core:detalle_cuenta_cobrar', pk=pk)

        if request.method == 'POST':
            form = PagoClienteForm(request.POST, cuenta=cuenta)
            if form.is_valid():
                try:
                    cuenta.registrar_pago(
                        monto_pago=form.cleaned_data['monto_bs'],
                        tasa_bcv=form.cleaned_data['tasa_bcv'],
                        referencia=form.cleaned_data['referencia'],
                        usuario=request.user,
                    )
                    AuditoriaAccion.registrar(
                        usuario=request.user, accion='pago_cliente',
                        descripcion=f'Pago Bs. {form.cleaned_data["monto_bs"]} de {cuenta.cliente} — Ref: {form.cleaned_data["referencia"]}',
                        request=request, objeto_tipo='CuentaPorCobrar', objeto_id=cuenta.pk,
                    )
                    messages.success(request, 'Pago registrado correctamente.')
                except ValueError as e:
                    messages.error(request, str(e))
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')
    return redirect('core:detalle_cuenta_cobrar', pk=pk)


# ══════════════════════════════════════════════
# CLIENTES
# ══════════════════════════════════════════════

@solo_admin
def lista_clientes(request):
    q = request.GET.get('q', '')
    clientes = Cliente.objects.all().order_by('apellido', 'nombre')
    if q:
        clientes = clientes.filter(
            Q(nombre__icontains=q) | Q(apellido__icontains=q) | Q(cedula_rif__icontains=q)
        )
    return render(request, 'core/clientes/lista.html', {'clientes': clientes, 'q': q})


@solo_admin
def crear_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save()
            messages.success(request, f'Cliente "{cliente.get_nombre_completo()}" registrado.')
            return redirect('core:lista_clientes')
    else:
        form = ClienteForm()
    return render(request, 'core/clientes/form.html', {'form': form, 'titulo': 'Nuevo cliente'})


@solo_admin
def editar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente actualizado.')
            return redirect('core:lista_clientes')
    else:
        form = ClienteForm(instance=cliente)
    return render(request, 'core/clientes/form.html', {
        'form': form, 'titulo': f'Editar: {cliente.get_nombre_completo()}'
    })