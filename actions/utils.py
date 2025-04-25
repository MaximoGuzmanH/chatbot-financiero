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

def get_entity(tracker, entity_name):
    """
    Extrae el valor de una entidad desde el tracker de Rasa.
    Si la entidad no se encuentra explícitamente, intenta recuperarla desde los slots.
    """
    for entity in tracker.latest_message.get("entities", []):
        if entity.get("entity") == entity_name:
            return entity.get("value")
    return tracker.get_slot(entity_name)
