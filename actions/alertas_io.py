import json
import os
import base64
from datetime import datetime
from typing import Dict, Any
import requests

RUTA_ALERTAS = "/tmp/alertas.json"

# --- GitHub Sync ---
GITHUB_REPO = "MaximoGuzmanH/chatbot-financiero"
ARCHIVO_ALERTAS = "alertas.json"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def subir_a_github_alertas():
    if not GITHUB_TOKEN:
        print("[WARN] GITHUB_TOKEN no definido. No se subirá a GitHub.")
        return

    try:
        with open(RUTA_ALERTAS, "r", encoding="utf-8") as f:
            contenido = f.read()

        contenido_base64 = base64.b64encode(contenido.encode("utf-8")).decode("utf-8")
        api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{ARCHIVO_ALERTAS}"

        response_get = requests.get(api_url, headers={"Authorization": f"Bearer {GITHUB_TOKEN}"})
        sha = response_get.json().get("sha") if response_get.status_code == 200 else None

        payload = {
            "message": "🟢 Actualización de alertas desde el bot",
            "content": contenido_base64,
            "branch": "main"
        }
        if sha:
            payload["sha"] = sha

        headers = {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json"
        }

        response = requests.put(api_url, headers=headers, json=payload)
        if response.status_code in [200, 201]:
            print("[SYNC] alertas.json actualizado en GitHub.")
        else:
            print(f"[ERROR] GitHub ({response.status_code}):", response.text)

    except Exception as e:
        print(f"[ERROR] al subir alertas: {e}")


def cargar_alertas(filtrar_activos=True):
    if not os.path.exists(RUTA_ALERTAS):
        return []
    try:
        with open(RUTA_ALERTAS, "r", encoding="utf-8") as f:
            alertas = json.load(f)
            return [a for a in alertas if a.get("status", 1) == 1] if filtrar_activos else alertas
    except json.JSONDecodeError:
        return []

import json, os

RUTA_ALERTAS = os.path.join(os.path.dirname(__file__), "alertas.json")

def guardar_alerta(alerta):
    alertas = cargar_alertas(filtrar_activos=False)
    
    # Asegurarse que la lista existe
    if not isinstance(alertas, list):
        alertas = []

    alerta["timestamp"] = datetime.now().isoformat()
    alerta["status"] = 1
    alertas.append(alerta)

    with open(RUTA_ALERTAS, "w", encoding="utf-8") as f:
        json.dump(alertas, f, ensure_ascii=False, indent=2)

    # 🔄 Sincronización (si quieres mantenerla)
    subir_a_github_alertas()

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

    for alerta in alertas:
        if alerta.get("status", 1) == 1:
            alerta["status"] = 0
            alerta["timestamp_modificacion"] = ahora.isoformat()

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


def actualizar_alerta_existente(condiciones: Dict[str, str], nueva_alerta: Dict[str, Any]) -> bool:
    ahora = datetime.now().isoformat()
    alertas = cargar_alertas(filtrar_activos=False)
    modificada = False

    for alerta in alertas:
        if (
            alerta.get("categoria", "").lower() == condiciones["categoria"].lower()
            and alerta.get("periodo", "").lower() == condiciones["periodo"].lower()
            and alerta.get("status", 1) == 1
        ):
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