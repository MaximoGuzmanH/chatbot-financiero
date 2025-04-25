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

# --- Recuperación inicial desde GitHub si no existe alerta local ---
def recuperar_alertas_desde_github():
    if not GITHUB_TOKEN:
        print("[WARN] GITHUB_TOKEN no definido. No se puede recuperar desde GitHub.")
        return

    api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{ARCHIVO_ALERTAS}"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}

    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        contenido_base64 = response.json().get("content", "")
        if contenido_base64:
            contenido_json = base64.b64decode(contenido_base64).decode("utf-8")
            with open(RUTA_ALERTAS, "w", encoding="utf-8") as f:
                f.write(contenido_json)
            print("[INIT] alertas.json restaurado desde GitHub.")
    else:
        print(f"[ERROR] No se pudo recuperar alertas desde GitHub: {response.status_code}")

# --- Inicialización local desde GitHub si no existe o está vacío ---
if not os.path.exists(RUTA_ALERTAS) or os.path.getsize(RUTA_ALERTAS) == 0:
    recuperar_alertas_desde_github()
    if not os.path.exists(RUTA_ALERTAS):  # Si aún no se creó, inicializar vacío
        with open(RUTA_ALERTAS, "w", encoding="utf-8") as f:
            json.dump([], f)

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
    with open(RUTA_ALERTAS, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [a for a in data if a.get("status", 1) == 1] if filtrar_activos else data

def guardar_alerta(alerta):
    alertas = cargar_alertas(filtrar_activos=False)
    alerta["timestamp"] = datetime.now().isoformat()
    alerta["status"] = 1
    alertas.append(alerta)

    with open(RUTA_ALERTAS, "w", encoding="utf-8") as f:
        json.dump(alertas, f, ensure_ascii=False, indent=2)

    subir_a_github_alertas()

def eliminar_alerta_logicamente(condiciones):
    recuperar_alertas_desde_github()
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

def modificar_alerta(condiciones: Dict[str, Any], nuevos_valores: Dict[str, Any]) -> bool:
    """
    Modifica una alerta existente activa según las condiciones dadas.
    """
    ahora = datetime.now().isoformat()

    # 🔁 Leer directamente del archivo para evitar trabajar con memoria cacheada
    if not os.path.exists(RUTA_ALERTAS):
        return False
    with open(RUTA_ALERTAS, "r", encoding="utf-8") as f:
        alertas = json.load(f)

    modificada = False
    for alerta in alertas:
        if (
            alerta.get("categoria", "").lower() == condiciones.get("categoria", "").lower()
            and alerta.get("periodo", "").lower() == condiciones.get("periodo", "").lower()
            and alerta.get("status", 1) == 1
        ):
            alerta.update(nuevos_valores)
            alerta["timestamp_modificacion"] = ahora
            modificada = True
            break

    if modificada:
        with open(RUTA_ALERTAS, "w", encoding="utf-8") as f:
            json.dump(alertas, f, ensure_ascii=False, indent=2)

        subir_a_github_alertas()

    return modificada
