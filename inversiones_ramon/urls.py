# ══════════════════════════════════════════════════════════════
# urls.py — Archivo principal del proyecto
# Ubicación: inversiones_ramon/urls.py
# ══════════════════════════════════════════════════════════════

from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect


urlpatterns = [

    # Admin de Django (solo para superusuario en desarrollo)
    path('django-admin/', admin.site.urls),

    # ── Módulo Core (auth + dashboard + usuarios + cuentas) ──
    path('', include('core.urls_core', namespace='core')),

    # ── Módulo Inventario ──
    path('inventario/', include('inventario.urls', namespace='inventario')),

    # ── Módulo Compras ──
    path('compras/', include('compras.urls', namespace='compras')),

    # ── Módulo Ventas ──
    path('ventas/', include('ventas.urls', namespace='ventas')),

    # ── Módulo Reportes ──
    path('reportes/', include('reportes.urls', namespace='reportes')),
]
