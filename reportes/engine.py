# ══════════════════════════════════════════════════════════════
# ENGINE — Motor de tendencias y cálculos DSS
# Consumido por las vistas de reportes
# ══════════════════════════════════════════════════════════════

from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal


# ─────────────────────────────────────────────
# 1. ALGORITMO DE VELOCIDAD DE VENTA
# Rango Corto (RC): últimos 7 días
# Rango Largo (RL): 21 días previos al RC
# Condición tendencia: vol_RC > promedio_semanal_RL * 1.20
# ─────────────────────────────────────────────

def calcular_tendencias():
    """
    Recorre todos los productos activos, aplica el algoritmo
    de velocidad de venta y actualiza el campo en_tendencia.
    Retorna lista de dicts con métricas por producto.
    """
    from inventario.models import Producto
    from ventas.models import DetalleVenta

    hoy      = date.today()
    inicio_rc = hoy - timedelta(days=7)
    inicio_rl = hoy - timedelta(days=28)   # 21 días antes del inicio del RC
    fin_rl    = inicio_rc - timedelta(days=1)

    resultados = []

    for producto in Producto.objects.filter(activo=True).select_related('categoria', 'proveedor'):

        # Volumen RC: unidades vendidas en últimos 7 días
        vol_rc = DetalleVenta.objects.filter(
            producto=producto,
            venta__fecha__gte=inicio_rc,
            venta__estado__in=['procesada', 'a_credito', 'pagada']
        ).aggregate(total=Sum('cantidad'))['total'] or 0

        # Volumen RL: unidades vendidas en los 21 días previos
        vol_rl = DetalleVenta.objects.filter(
            producto=producto,
            venta__fecha__gte=inicio_rl,
            venta__fecha__lte=fin_rl,
            venta__estado__in=['procesada', 'a_credito', 'pagada']
        ).aggregate(total=Sum('cantidad'))['total'] or 0

        # Promedio semanal histórico (RL / 3 semanas)
        promedio_semanal_rl = Decimal(str(vol_rl)) / Decimal('3')

        # Condición: aceleración del 20%
        umbral      = promedio_semanal_rl * Decimal('1.20')
        en_tendencia = vol_rc > umbral and vol_rc > 0

        # Actualizar campo en BD
        if producto.en_tendencia != en_tendencia:
            producto.en_tendencia = en_tendencia
            producto.save(update_fields=['en_tendencia'])

        # Proyección lineal para 2 semanas
        promedio_diario = Decimal(str(vol_rc)) / Decimal('7')
        cantidad_sugerida_2sem = max(
            int((promedio_diario * 14) - producto.stock_actual),
            producto.stock_minimo
        )

        resultados.append({
            'producto':             producto,
            'vol_rc':               vol_rc,
            'vol_rl':               vol_rl,
            'promedio_semanal_rl':  round(float(promedio_semanal_rl), 2),
            'umbral':               round(float(umbral), 2),
            'en_tendencia':         en_tendencia,
            'cantidad_sugerida_2sem': cantidad_sugerida_2sem,
        })

    return sorted(resultados, key=lambda x: x['vol_rc'], reverse=True)


# ─────────────────────────────────────────────
# 2. PANEL DE ABASTECIMIENTO CRÍTICO
# Productos en tendencia o bajo stock por proveedor
# ─────────────────────────────────────────────

def panel_abastecimiento(proveedor_id=None):
    """
    Retorna productos que necesitan reposición urgente,
    agrupados por proveedor, con cantidad sugerida para 2 semanas.
    """
    from inventario.models import Producto
    from ventas.models import DetalleVenta

    hoy       = date.today()
    hace_7    = hoy - timedelta(days=7)

    qs = Producto.objects.filter(activo=True).select_related('proveedor', 'categoria')
    if proveedor_id:
        qs = qs.filter(proveedor_id=proveedor_id)

    criticos = []
    for p in qs:
        bajo_stock   = p.stock_actual <= p.stock_minimo
        en_tendencia = getattr(p, 'en_tendencia', False)

        if not (bajo_stock or en_tendencia):
            continue

        vol_7d = DetalleVenta.objects.filter(
            producto=p,
            venta__fecha__gte=hace_7,
            venta__estado__in=['procesada', 'a_credito', 'pagada']
        ).aggregate(t=Sum('cantidad'))['t'] or 0

        prom_diario = Decimal(str(vol_7d)) / Decimal('7')
        sugerido    = max(int(prom_diario * 14) - p.stock_actual, p.stock_minimo)

        criticos.append({
            'producto':    p,
            'bajo_stock':  bajo_stock,
            'en_tendencia': en_tendencia,
            'vol_7d':      vol_7d,
            'sugerido':    sugerido,
        })

    return sorted(criticos, key=lambda x: (not x['en_tendencia'], x['producto'].stock_actual))


# ─────────────────────────────────────────────
# 3. REPORTE DE VENTAS POR PERÍODO
# ─────────────────────────────────────────────

def reporte_ventas(fecha_inicio, fecha_fin):
    from ventas.models import Venta, DetalleVenta

    ventas = Venta.objects.filter(
        fecha__gte=fecha_inicio,
        fecha__lte=fecha_fin,
        estado__in=['procesada', 'a_credito', 'pagada']
    )

    totales = ventas.aggregate(
        total_bs  = Sum('total_bs'),
        total_usd = Sum('total_usd'),
        cantidad  = Count('id'),
    )

    # Ventas por día
    from django.db.models.functions import TruncDate
    por_dia = (
        ventas
        .annotate(dia=TruncDate('fecha'))
        .values('dia')
        .annotate(total=Sum('total_bs'), cantidad=Count('id'))
        .order_by('dia')
    )

    # Top productos
    top_productos = (
        DetalleVenta.objects.filter(
            venta__fecha__gte=fecha_inicio,
            venta__fecha__lte=fecha_fin,
            venta__estado__in=['procesada', 'a_credito', 'pagada']
        )
        .values('producto__nombre', 'producto__codigo')
        .annotate(
            unidades = Sum('cantidad'),
            ingresos = Sum('subtotal'),
        )
        .order_by('-unidades')[:10]
    )

    # Por método de pago
    por_metodo = (
        ventas
        .values('metodo_pago')
        .annotate(total=Sum('total_bs'), cantidad=Count('id'))
        .order_by('-total')
    )

    return {
        'ventas':        ventas,
        'totales':       totales,
        'por_dia':       list(por_dia),
        'top_productos': list(top_productos),
        'por_metodo':    list(por_metodo),
        'fecha_inicio':  fecha_inicio,
        'fecha_fin':     fecha_fin,
    }


# ─────────────────────────────────────────────
# 4. REPORTE DE COMPRAS POR PERÍODO
# ─────────────────────────────────────────────

def reporte_compras(fecha_inicio, fecha_fin):
    from compras.models import Compra

    compras = Compra.objects.filter(
        fecha_creacion__date__gte=fecha_inicio,
        fecha_creacion__date__lte=fecha_fin,
        estado='recibida'
    ).select_related('proveedor')

    totales = compras.aggregate(
        total_bs = Sum('total'),
        cantidad = Count('id'),
    )

    por_proveedor = (
        compras
        .values('proveedor__nombre')
        .annotate(total=Sum('total'), cantidad=Count('id'))
        .order_by('-total')
    )

    pendientes_pago = compras.filter(
        modalidad_pago='credito', pagado=False
    ).aggregate(deuda=Sum('total'))['deuda'] or Decimal('0')

    return {
        'compras':          compras,
        'totales':          totales,
        'por_proveedor':    list(por_proveedor),
        'pendientes_pago':  pendientes_pago,
        'fecha_inicio':     fecha_inicio,
        'fecha_fin':        fecha_fin,
    }


# ─────────────────────────────────────────────
# 5. REPORTE DE INVENTARIO
# ─────────────────────────────────────────────

def reporte_inventario():
    from inventario.models import Producto

    productos = Producto.objects.filter(activo=True).select_related('categoria', 'proveedor')

    # Valoración patrimonial (stock * precio_compra)
    from django.db.models import F, ExpressionWrapper, DecimalField
    valorizacion = (
        productos
        .annotate(
            valor = ExpressionWrapper(
                F('stock_actual') * F('precio_compra'),
                output_field=DecimalField()
            )
        )
        .aggregate(total=Sum('valor'))['total'] or Decimal('0')
    )

    bajo_stock   = [p for p in productos if p.stock_bajo]
    en_tendencia = [p for p in productos if getattr(p, 'en_tendencia', False)]

    por_categoria = (
        productos
        .values('categoria__nombre')
        .annotate(cantidad=Count('id'), stock_total=Sum('stock_actual'))
        .order_by('-stock_total')
    )

    return {
        'productos':      productos,
        'valorizacion':   valorizacion,
        'bajo_stock':     bajo_stock,
        'en_tendencia':   en_tendencia,
        'por_categoria':  list(por_categoria),
        'total_productos': productos.count(),
    }
