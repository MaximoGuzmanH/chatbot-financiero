# 🤖 Chatbot de Finanzas Personales con Rasa + Streamlit

Este proyecto integra un chatbot de finanzas personales construido con [Rasa](https://rasa.com) y desplegado en línea mediante [Streamlit Community Cloud](https://streamlit.io/cloud), utilizando un túnel seguro con [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/).

---

## 📦 Estructura del Proyecto

```bash
chatbot-finanzas/
├── actions/
│   ├── actions.py
│   ├── transacciones_io.py
│   └── alertas_io.py
├── data/
│   ├── nlu.yml
│   ├── rules.yml
│   └── stories.yml
├── domain.yml
├── config.yml
├── credentials.yml
├── endpoints.yml
├── models/
├── streamlit_app/
│   └── app.py
├── alertas.json
├── transacciones.json
├── README.md


## 🧩 Requisitos Previos

Python 3.10

pip

Cloudflared


## 🛠️ Instalación y Configuración

Cuenta gratuita en Streamlit Community Cloud

# Clona el repositorio
git clone https://github.com/tu-usuario/chatbot-finanzas.git
cd chatbot-finanzas

# Crea entorno virtual
python -m venv venv
source venv/bin/activate  # En Linux/Mac
venv\Scripts\activate     # En Windows

# Instala dependencias
pip install -r requirements.txt

# Entrena el modelo Rasa
rasa train


##🚀 Ejecutar el Chatbot con Cloudflare Tunnel

1. Inicia Rasa:

rasa run --enable-api --cors "*" --debug

2. En una segunda terminal (misma carpeta), inicia el túnel:

cloudflared tunnel --url http://localhost:5005

3. Copia la URL generada (ej. https://glowing-tunnel.trycloudflare.com)


## 🌐 Ejecutar Interfaz Streamlit

Edita streamlit_app/app.py y reemplaza esta línea con la URL generada por Cloudflare:

    RASA_URL = "https://glowing-tunnel.trycloudflare.com/webhooks/rest/webhook"

Luego:

    streamlit run streamlit_app/app.py

Y abre el navegador en: http://localhost:8501


## 🧪 Pruebas

rasa data validate
rasa shell


## 👨‍💻 Desarrollado por

    Maximo Guzman Huaman
    Sergio Renato Zegarra Villanueva

Este proyecto busca facilitar la gestión de finanzas personales mediante inteligencia artificial conversacional.

