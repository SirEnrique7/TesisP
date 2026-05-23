from django.contrib import admin
from .models import Producto, Categoria, Proveedor, MovimientoInventario, SolicitudInventario

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display  = ['codigo', 'nombre', 'categoria', 'stock_actual', 'stock_minimo', 'en_tendencia', 'activo']
    list_filter   = ['categoria', 'activo', 'en_tendencia']
    search_fields = ['nombre', 'codigo']

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'descripcion']

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display  = ['nombre', 'rif', 'dia_visita', 'telefono']
    search_fields = ['nombre', 'rif']

@admin.register(MovimientoInventario)
class MovimientoAdmin(admin.ModelAdmin):
    list_display    = ['fecha', 'producto', 'tipo', 'cantidad', 'usuario']
    list_filter     = ['tipo']
    readonly_fields = ['fecha']

@admin.register(SolicitudInventario)
class SolicitudAdmin(admin.ModelAdmin):
    list_display = ['id', 'empleado', 'producto', 'cantidad_solicitada', 'estado', 'fecha_solicitud']
    list_filter  = ['estado']
