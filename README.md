# 🤖 Chatbot Financiero con Rasa y Streamlit

Este proyecto integra un asistente conversacional para la gestión de finanzas personales, construido con Rasa y una interfaz web desarrollada en Streamlit. 
Ambos servicios están desplegados en la plataforma Render, permitiendo una interacción fluida y en línea.

---

## 📦 Estructura del Proyecto

chatbot-financiero/
├── actions/
│   ├── actions.py
│   ├── transacciones_io.py
│   ├── alertas_io.py
│   ├── requirements.txt
│   └── Dockerfile
├── data/
│   ├── nlu.yml
│   ├── rules.yml
│   └── stories.yml
├── models/
├── streamlit_app/
│   └── app.py
├── alertas.json
├── transacciones.json
├── config.yml
├── credentials.yml
├── endpoints.yml
├── README.md
└── requirements.txt


## ⚙️ Requisitos Previos

- Python 3.10
- pip
- Cuenta en Render
- Cuenta en Streamlit Community Cloud (opcional)

## 🚀 Despliegue en Render (Producción)

1. Backend de Acciones Personalizadas (actions-server)
 - Se despliega desde la carpeta actions/, usando su propio Dockerfile.
 - Debe exponerse en el puerto 5055.
 - Al desplegar, Render entregará una URL pública como:

    https://actions-server-1wwf.onrender.com

2. Servidor Principal de Rasa (chatbot-financiero)
 - Debe estar conectado al servidor de acciones, editando endpoints.yml:

    action_endpoint:
    url: "https://actions-server-xxxx.onrender.com/webhook"

 - El servicio principal se ejecuta con:

    rasa run --enable-api --cors "*" --debug

 - Render asignará una URL pública como:

    https://chatbot-financiero.onrender.com

3. Frontend con Streamlit (opcional)
 - Streamlit puede ejecutarse localmente o desplegarse en Streamlit Community Cloud.
 - Edita en app.py la URL del endpoint:

    RASA_ENDPOINT = "https://chatbot-financiero.onrender.com/webhooks/rest/webhook"

## 🧪 Pruebas y Validación
 - Validar los datos de entrenamiento:

    rasa data validate

 - Probar el chatbot en la línea de comandos:

    rasa shell

## 💬 Interfaz de Usuario con Streamlit
 - Navega a la carpeta streamlit_app/.
 - Asegúrate de que el archivo app.py esté configurado para apuntar al servidor de Rasa desplegado:

    RASA_ENDPOINT = "https://chatbot-financiero.onrender.com/webhooks/rest/webhook"

 - Ejecuta la aplicación localmente con:

    streamlit run app.py

La interfaz estará disponible en: http://localhost:8501

Nota: También puedes desplegar la aplicación Streamlit en Streamlit Community Cloud (https://streamlit.io/cloud) para acceso en línea.

## 🛠️ Instalación y Ejecución Local (Desarrollo)
 - Requisitos
   - Python 3.10
   - pip
   - Cuenta en Streamlit Cloud (opcional)

 - Instalación
    # Clona el repositorio
    git clone https://github.com/MaximoGuzmanH/chatbot-financiero.git
    cd chatbot-financiero

    # Crea un entorno virtual
    python -m venv venv
    source venv/bin/activate        # Linux/Mac
    venv\Scripts\activate           # Windows

    # Instala dependencias
    pip install -r requirements.txt

    # Entrena el modelo
    rasa train

 - Ejecutar Interfaz Streamlit (local)
   
    streamlit run streamlit_app/app.py

 - Abre el navegador en: http://localhost:8501


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


## 🧪 Pruebas

rasa data validate
rasa shell


## 👨‍💻 Desarrollado por

    Maximo Guzman Huaman
    Sergio Renato Zegarra Villanueva

Este proyecto busca facilitar la gestión de finanzas personales mediante inteligencia artificial conversacional.