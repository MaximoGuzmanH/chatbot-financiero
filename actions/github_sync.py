import os
import base64
import requests
import logging
from datetime import datetime

# ---------- CONFIGURACIÓN DE LOG ----------
fecha_log = datetime.now().strftime("%Y-%m-%d")
logs_dir = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(logs_dir, exist_ok=True)
LOG_PATH = os.path.join(logs_dir, f"github_sync_{fecha_log}.log")
RUTA_DESTINO_LOG = f"logs/github_sync_{fecha_log}.log"

logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# ---------- VARIABLES DE ENTORNO ----------
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
GITHUB_REPO = os.getenv("GITHUB_REPO")

GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/"

# ---------- FUNCIÓN DE SUBIDA ----------
def subir_a_github(ruta_archivo_local: str, ruta_destino_repo: str, mensaje_commit: str):
    if not all([GITHUB_TOKEN, GITHUB_USERNAME, GITHUB_REPO]):
        msg = "[ERROR] Faltan variables de entorno para autenticación con GitHub."
        print(msg)
        logging.error(msg)
        return False

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    # Leer archivo local
    try:
        with open(ruta_archivo_local, "rb") as f:
            contenido = f.read()
        contenido_base64 = base64.b64encode(contenido).decode("utf-8")
    except Exception as e:
        msg = f"[ERROR] No se pudo leer el archivo local: {e}"
        print(msg)
        logging.error(msg)
        return False

    # Verificar existencia para obtener SHA
    url_archivo = GITHUB_API_URL + ruta_destino_repo
    response = requests.get(url_archivo, headers=headers)
    sha = response.json().get("sha") if response.status_code == 200 else None

    # Armar payload
    payload = {
        "message": mensaje_commit,
        "content": contenido_base64,
        "branch": "main"
    }
    if sha:
        payload["sha"] = sha

    # PUT a GitHub
    response = requests.put(url_archivo, headers=headers, json=payload)

    if response.status_code in [200, 201]:
        msg = f"[OK] Archivo actualizado en GitHub: {ruta_destino_repo}"
        print(msg)
        logging.info(msg)

        # ---- Subir el LOG TAMBIÉN ----
        try:
            if os.path.exists(LOG_PATH):
                with open(LOG_PATH, "rb") as log_f:
                    log_content = base64.b64encode(log_f.read()).decode("utf-8")

                log_payload = {
                    "message": f"📝 Log automático: {RUTA_DESTINO_LOG}",
                    "content": log_content,
                    "branch": "main"
                }

                log_url = GITHUB_API_URL + RUTA_DESTINO_LOG
                log_resp = requests.get(log_url, headers=headers)
                log_sha = log_resp.json().get("sha") if log_resp.status_code == 200 else None
                if log_sha:
                    log_payload["sha"] = log_sha

                log_response = requests.put(log_url, headers=headers, json=log_payload)
                if log_response.status_code in [200, 201]:
                    logging.info(f"[OK] Log sincronizado: {RUTA_DESTINO_LOG}")
                else:
                    logging.warning(f"[WARN] Fallo al sincronizar log: {log_response.status_code} - {log_response.text}")
        except Exception as e:
            logging.error(f"[ERROR] No se pudo sincronizar el log: {e}")

        return True

    else:
        msg = f"[ERROR] Fallo al subir archivo: {response.status_code} - {response.text}"
        print(msg)
        logging.error(msg)
        return False