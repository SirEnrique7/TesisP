# ══════════════════════════════════════════════════════════════
# CONTEXT PROCESSOR — Inyecta tasa BCV en todos los templates
# Registrar en TEMPLATES > OPTIONS > context_processors
# ══════════════════════════════════════════════════════════════

from .models import TasaCambio


def tasa_bcv(request):
    """Disponible como {{ tasa_bcv }} en cualquier template."""
    if request.user.is_authenticated:
        try:
            return {'tasa_bcv': TasaCambio.tasa_vigente()}
        except Exception:
            # Si la tabla está vacía o la BD falla, el sistema sigue vivo
            return {'tasa_bcv': None}
            
    return {'tasa_bcv': None}