from django.contrib import admin
from .models import Compra, DetalleCompra

@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    list_display    = ['numero_referencia', 'proveedor', 'estado', 'modalidad_pago', 'pagado', 'total']
    list_filter     = ['estado', 'modalidad_pago', 'pagado']
    search_fields   = ['numero_referencia', 'proveedor__nombre']
    readonly_fields = ['numero_referencia', 'fecha_creacion']
