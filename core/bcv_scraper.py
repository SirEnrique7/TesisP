# ══════════════════════════════════════════════════════════════
# BCV SCRAPER — Extracción automática de la tasa oficial (CORREGIDO)
# ══════════════════════════════════════════════════════════════

import requests
import re
import urllib3
from decimal import Decimal, InvalidOperation
from django.utils import timezone

# Silenciar las advertencias de SSL inseguro (necesario por el verify=False del BCV)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def extraer_tasa_bcv() -> Decimal | None:
    """
    Realiza HTTP GET a bcv.org.ve ignorando errores de certificados SSL,
    extrae el valor del USD mediante expresiones regulares flexibles.
    """
    url     = 'https://www.bcv.org.ve/'
    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        )
    }

    try:
        # CORRECCIÓN: verify=False evita que el scraper muera por fallos de certificados del BCV
        resp = requests.get(url, headers=headers, timeout=15, verify=False)
        resp.raise_for_status()

        # CORRECCIÓN: Un patrón mucho más elástico. 
        # Busca el contenedor del dólar y extrae el primer número decimal formateado con comas que encuentre cerca.
        patron = r'id=["\']dolar["\'].*?([\d]{2,3},[\d]{2,4})'
        match  = re.search(patron, resp.text, re.DOTALL | re.IGNORECASE)

        if not match:
            # Fallback elástico: Buscar la palabra USD seguida de cualquier estructura numérica venezolana
            patron2 = r'USD.*?([\d\.,]+,\d{2,4})'
            match   = re.search(patron2, resp.text, re.DOTALL | re.IGNORECASE)

        if match:
            raw = match.group(1).strip()
            
            # Normalización robusta de la nomenclatura monetaria venezolana
            # Eliminamos los puntos de miles si existen y cambiamos la coma decimal por punto.
            raw = raw.replace('.', '').replace(',', '.')
            
            return Decimal(raw)

    except (requests.RequestException, InvalidOperation):
        # Evitamos el uso de 'pass' plano para mantener buenas prácticas de depuración
        return None

    return None


def actualizar_tasa_hoy():
    """
    Verifica si ya existe tasa para hoy.
    Si no, extrae del BCV y la persiste en TasaCambio.
    """
    from core.models import TasaCambio, AuditoriaAccion

    hoy = timezone.now().date()

    # Ya existe para hoy → no extraer de nuevo
    existente = TasaCambio.objects.filter(fecha=hoy).first()
    if existente:
        return existente.tasa_bs_usd, False

    tasa = extraer_tasa_bcv()
    if tasa:
        registro = TasaCambio.objects.create(
            fecha       = hoy,
            tasa_bs_usd = tasa,
            fuente      = 'bcv.org.ve',
        )
        
        # Guardamos en la auditoría del sistema la acción automatizada
        # Nota: Asegúrate de que tu método registrar acepte usuario=None para tareas del sistema
        try:
            AuditoriaAccion.registrar(
                usuario     = None,
                accion      = 'tasa_bcv',
                descripcion = f'Tasa BCV actualizada automáticamente: Bs. {tasa} / USD',
            )
        except Exception:
            pass # Previene que un fallo en el log detenga la creación de la tasa
            
        return tasa, True

    # Si falla el scraping por completo, usar la última tasa disponible como salvavidas
    ultima = TasaCambio.objects.order_by('-fecha').first()
    if ultima:
        return ultima.tasa_bs_usd, False

    return None, False