import json
import os
from datetime import datetime
from typing import Dict, Any
import requests

RUTA_ALERTAS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "alertas.json")

# --- GitHub Sync (producción en Render) ---
GITHUB_REPO = "MaximoGuzmanH/chatbot-financiero"
ARCHIVO_ALERTAS = "alertas.json"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def cargar_alertas(filtrar_activos=True):
    if not os.path.exists(RUTA_ALERTAS):
        return []
    try:
        with open(RUTA_ALERTAS, "r", encoding="utf-8") as f:
            alertas = json.load(f)
            if filtrar_activos:
                alertas = [a for a in alertas if a.get("status", 1) == 1]
            return alertas
    except json.JSONDecodeError:
        return []


def guardar_alerta(alerta):
    alertas = cargar_alertas(filtrar_activos=False)
    alerta["timestamp"] = datetime.now().isoformat()
    alerta["status"] = 1
    alertas.append(alerta)

    with open(RUTA_ALERTAS, "w", encoding="utf-8") as f:
        json.dump(alertas, f, ensure_ascii=False, indent=2)

    subir_a_github_alertas()
    
    from github_sync import subir_a_github

    subir_a_github(
        ruta_archivo_local=RUTA_ALERTAS,
        ruta_destino_repo="alertas.json",
        mensaje_commit="Actualización automática de alertas desde Streamlit"
    )



def eliminar_alerta_logicamente(condiciones):
    alertas = cargar_alertas(filtrar_activos=False)
    modificada = False
    for alerta in alertas:
        if all(alerta.get(k) == v for k, v in condiciones.items()) and alerta.get("status", 1) == 1:
            alerta["status"] = 0
            alerta["timestamp_modificacion"] = datetime.now().isoformat()
            modificada = True
            break
    if modificada:
        with open(RUTA_ALERTAS, "w", encoding="utf-8") as f:
            json.dump(alertas, f, ensure_ascii=False, indent=2)
        subir_a_github_alertas()


def guardar_todas_las_alertas(nuevas_alertas):
    ahora = datetime.now()
    alertas = cargar_alertas(filtrar_activos=False)

    # Desactivar todas las alertas activas
    for alerta in alertas:
        if alerta.get("status", 1) == 1:
            alerta["status"] = 0
            alerta["timestamp_modificacion"] = ahora.isoformat()

    # Agregar nuevas alertas activas
    for nueva in nuevas_alertas:
        nueva_alerta = {
            "categoria": nueva["categoria"],
            "monto": nueva["monto"],
            "periodo": nueva["periodo"],
            "status": 1,
            "timestamp": ahora.isoformat()
        }
        alertas.append(nueva_alerta)

    with open(RUTA_ALERTAS, "w", encoding="utf-8") as f:
        json.dump(alertas, f, ensure_ascii=False, indent=2)

    subir_a_github_alertas()

    from github_sync import subir_a_github

    subir_a_github(
        ruta_archivo_local=RUTA_ALERTAS,
        ruta_destino_repo="alertas.json",
        mensaje_commit="Actualización automática de alertas desde Streamlit"
    )

def actualizar_alerta_existente(condiciones: Dict[str, str], nueva_alerta: Dict[str, Any]) -> bool:
    ahora = datetime.now().isoformat()
    alertas = cargar_alertas(filtrar_activos=False)

    modificada = False
    for alerta in alertas:
        if (alerta.get("categoria", "").lower() == condiciones["categoria"].lower()
                and alerta.get("periodo", "").lower() == condiciones["periodo"].lower()
                and alerta.get("status", 1) == 1):
            alerta["status"] = 0
            alerta["timestamp_modificacion"] = ahora
            modificada = True

    if modificada:
        nueva_alerta["status"] = 1
        nueva_alerta["timestamp"] = ahora
        alertas.append(nueva_alerta)

        with open(RUTA_ALERTAS, "w", encoding="utf-8") as f:
            json.dump(alertas, f, ensure_ascii=False, indent=2)

        subir_a_github_alertas()

    return modificada
