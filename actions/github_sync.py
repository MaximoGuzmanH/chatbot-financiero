import os
import base64
import requests
from datetime import datetime

# Cargamos los secrets desde variables de entorno
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
GITHUB_REPO = os.getenv("GITHUB_REPO")

GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/"

def subir_a_github(ruta_archivo_local: str, ruta_destino_repo: str, mensaje_commit: str):
    if not all([GITHUB_TOKEN, GITHUB_USERNAME, GITHUB_REPO]):
        print("[ERROR] Faltan variables de entorno para autenticación con GitHub.")
        return False

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    # Leer contenido del archivo local
    try:
        with open(ruta_archivo_local, "rb") as f:
            contenido = f.read()
        contenido_base64 = base64.b64encode(contenido).decode("utf-8")
    except Exception as e:
        print(f"[ERROR] No se pudo leer el archivo local: {e}")
        return False

    # Verificar si ya existe
    url_archivo = GITHUB_API_URL + ruta_destino_repo
    response = requests.get(url_archivo, headers=headers)
    if response.status_code == 200:
        sha = response.json().get("sha")
    else:
        sha = None

    # Payload para crear o actualizar el archivo
    payload = {
        "message": mensaje_commit,
        "content": contenido_base64,
        "branch": "main"
    }
    if sha:
        payload["sha"] = sha

    # Hacer PUT a GitHub
    response = requests.put(url_archivo, headers=headers, json=payload)
    if response.status_code in [200, 201]:
        print(f"[INFO] Archivo actualizado correctamente: {ruta_destino_repo}")
        return True
    else:
        print(f"[ERROR] Fallo al actualizar archivo: {response.status_code} - {response.text}")
        return False
