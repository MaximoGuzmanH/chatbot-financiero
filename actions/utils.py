# actions/utils.py

import re

def parse_monto(monto_str):
    """
    Extrae el valor numérico del string del monto.
    """
    try:
        monto_limpio = re.sub(r"[^\d.]", "", monto_str.replace(",", "."))
        return float(monto_limpio)
    except Exception:
        raise ValueError("Monto inválido")

def construir_mensaje(*lineas):
    """
    Construye un mensaje en Markdown con saltos de línea HTML.
    """
    return "<br>".join(lineas)
