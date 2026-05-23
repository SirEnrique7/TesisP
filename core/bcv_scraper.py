# ══════════════════════════════════════════════════════════════
# BCV SCRAPER — Extracción automática de la tasa oficial
# Se ejecuta una vez por día al primer login
# ══════════════════════════════════════════════════════════════

import requests
import re
from decimal import Decimal, InvalidOperation
from django.utils import timezone


def extraer_tasa_bcv() -> Decimal | None:
    """
    Realiza HTTP GET a bcv.org.ve, extrae el valor del USD
    mediante expresión regular sobre el HTML devuelto.
    Retorna Decimal con la tasa o None si falla.
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
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()

        # El BCV publica el dólar en un elemento con id="dolar"
        # Buscamos el número dentro de ese bloque
        patron = r'id=["\']dolar["\'][^>]*>.*?<strong>([\d,\.]+)</strong>'
        match  = re.search(patron, resp.text, re.DOTALL | re.IGNORECASE)

        if not match:
            # Fallback: buscar strong con formato de precio venezolano
            patron2 = r'USD.*?<strong>([\d]{1,3}(?:[,\.]\d{3})*(?:[,\.]\d{1,2})?)</strong>'
            match   = re.search(patron2, resp.text, re.DOTALL | re.IGNORECASE)

        if match:
            raw   = match.group(1).strip()
            # Normalizar: Venezuela usa coma como decimal
            # Ej: "36,45" → "36.45"  |  "1.036,45" → "1036.45"
            if ',' in raw and '.' in raw:
                raw = raw.replace('.', '').replace(',', '.')
            elif ',' in raw:
                raw = raw.replace(',', '.')

            return Decimal(raw)

    except requests.RequestException:
        pass
    except InvalidOperation:
        pass

    return None


def actualizar_tasa_hoy():
    """
    Verifica si ya existe tasa para hoy.
    Si no, extrae del BCV y la persiste en TasaCambio.
    Retorna (tasa_decimal, es_nueva) o (None, False) si falla.
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
        AuditoriaAccion.registrar(
            usuario     = None,
            accion      = 'tasa_bcv',
            descripcion = f'Tasa BCV actualizada automáticamente: Bs. {tasa} / USD',
        )
        return tasa, True

    # Si falla el scraping, usar la última tasa disponible como fallback
    ultima = TasaCambio.objects.order_by('-fecha').first()
    if ultima:
        return ultima.tasa_bs_usd, False

    return None, False
