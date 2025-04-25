import json
import os
from datetime import datetime
import requests
import base64

# Ruta local al archivo transacciones.json dentro del contenedor
RUTA_TRANSACCIONES = "/tmp/transacciones.json"

# GitHub API
REPO = "MaximoGuzmanH/chatbot-financiero"
ARCHIVO_GITHUB = "transacciones.json"
TOKEN = os.getenv("GITHUB_TOKEN")
SINCRONIZADO = False  # Indica si ya se descargó el archivo desde GitHub

# Constante global reutilizable
MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
]

def subir_a_github(ruta_local, repo, archivo_remoto, token):
    if not token:
        print("[WARN] TOKEN de GitHub no disponible. No se subirá el archivo.")
        return

    with open(ruta_local, "r", encoding="utf-8") as f:
        contenido = f.read()

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json"
    }

    url_base = f"https://api.github.com/repos/{repo}/contents/{archivo_remoto}"

    resp = requests.get(url_base, headers=headers)
    sha = resp.json().get("sha") if resp.status_code == 200 else None

    payload = {
        "message": f"Actualización automática de {archivo_remoto}",
        "content": base64.b64encode(contenido.encode()).decode("utf-8"),
        "branch": "main"
    }
    if sha:
        payload["sha"] = sha

    response = requests.put(url_base, headers=headers, json=payload)
    if response.status_code not in [200, 201]:
        print(f"[ERROR] GitHub update failed: {response.status_code} - {response.text}")
    else:
        print(f"[OK] Archivo {archivo_remoto} actualizado en GitHub")

def descargar_de_github():
    global SINCRONIZADO
    url = f"https://raw.githubusercontent.com/{REPO}/main/{ARCHIVO_GITHUB}"

    try:
        response = requests.get(url)
        if response.status_code == 200:
            nuevo_contenido = response.text

            # ❌ No sobrescribimos si el archivo remoto está vacío
            if not nuevo_contenido.strip():
                print("[WARN] El archivo remoto está vacío. No se sobrescribirá localmente.")
                return False

            # 🧼 Siempre eliminamos el archivo local antes de sobrescribir
            if os.path.exists(RUTA_TRANSACCIONES):
                try:
                    os.remove(RUTA_TRANSACCIONES)
                    print("[INFO] Archivo transacciones.json eliminado localmente antes de sincronizar.")
                except Exception as e:
                    print(f"[ERROR] No se pudo eliminar archivo local: {e}")

            # 💾 Guardamos el nuevo contenido descargado
            with open(RUTA_TRANSACCIONES, "w", encoding="utf-8") as f:
                f.write(nuevo_contenido)

            SINCRONIZADO = True
            print("[INFO] transacciones.json sincronizado correctamente desde GitHub")
            return True

        else:
            print(f"[WARN] No se pudo descargar el archivo desde GitHub ({response.status_code})")
            return False

    except Exception as e:
        print(f"[ERROR] Al intentar sincronizar desde GitHub: {e}")
        return False

def cargar_transacciones(filtrar_activos=True, sincronizar=True):
    if sincronizar:
        if not descargar_de_github():
            print("[ERROR] No se pudo sincronizar transacciones antes de consulta")
            return []

    if not os.path.exists(RUTA_TRANSACCIONES):
        return []

    try:
        with open(RUTA_TRANSACCIONES, "r", encoding="utf-8") as f:
            transacciones = json.load(f)
            return [t for t in transacciones if t.get("status", 1) == 1] if filtrar_activos else transacciones
    except json.JSONDecodeError:
        return []

def guardar_transaccion(transaccion):
    # 🔄 Paso 1: sincronizar antes de cualquier lectura
    descargar_de_github()  # Esto descarga desde GitHub y pisa el archivo local

    # 📥 Paso 2: cargar lo que ahora está en local (ya sincronizado)
    try:
        transacciones = cargar_transacciones(filtrar_activos=False, sincronizar=False)
    except Exception as e:
        print(f"[ERROR] No se pudo cargar transacciones previas: {e}")
        transacciones = []

    # 🧱 Paso 3: agregar los campos auxiliares (fecha, timestamp, etc.)
    ahora = datetime.now()
    fecha_str = transaccion.get("fecha") or ahora.strftime("%d/%m/%Y")

    try:
        if "de" in fecha_str:
            partes = fecha_str.lower().split(" de ")
            dia = int(partes[0])
            mes = partes[1]
            año = ahora.year
        else:
            dia, mes_num, año = map(int, fecha_str.split("/"))
            mes = MESES[mes_num - 1]
    except:
        dia = ahora.day
        mes = ahora.strftime("%B").lower()
        año = ahora.year

    transaccion.update({
        "dia": dia,
        "mes": mes,
        "año": año,
        "timestamp": ahora.isoformat(),
        "status": transaccion.get("status", 1)
    })

    # ➕ Paso 4: agregar la nueva transacción a la lista sincronizada
    transacciones.append(transaccion)

    # 💾 Paso 5: guardar en el archivo local
    with open(RUTA_TRANSACCIONES, "w", encoding="utf-8") as f:
        json.dump(transacciones, f, ensure_ascii=False, indent=2)

    # ☁️ Paso 6: subir la nueva versión a GitHub
    from github_sync import subir_log_a_github
    subir_log_a_github(
        ruta_archivo_local=RUTA_TRANSACCIONES,
        ruta_destino_repo=ARCHIVO_GITHUB,
        mensaje_commit="Ingreso registrado automáticamente"
    )


def eliminar_transaccion_logicamente(condiciones):
    transacciones = cargar_transacciones(filtrar_activos=False)
    modificada = False

    for transaccion in transacciones:
        if transaccion.get("status", 1) == 0:
            continue
        if all(transaccion.get(k) == v for k, v in condiciones.items()):
            transaccion["status"] = 0
            transaccion["timestamp_modificacion"] = datetime.now().isoformat()
            modificada = True
            break

    if modificada:
        with open(RUTA_TRANSACCIONES, "w", encoding="utf-8") as f:
            json.dump(transacciones, f, ensure_ascii=False, indent=2)
        print(f"[INFO] Eliminada lógicamente: {condiciones}")
        if TOKEN:
            subir_a_github(RUTA_TRANSACCIONES, REPO, ARCHIVO_GITHUB, TOKEN)
    else:
        print(f"[WARN] No encontrada: {condiciones}")

# 🔁 Cargar desde GitHub si no existe en el contenedor (primer arranque)
if not os.path.exists(RUTA_TRANSACCIONES):
    descargar_de_github()
