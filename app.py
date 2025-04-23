import streamlit as st
import requests
from datetime import datetime
import pytz

# 🧹 Botón flotante funcional en Streamlit
import streamlit.components.v1 as components

# 🔗 Configuración del endpoint
RASA_ENDPOINT = "https://chatbot-financiero.onrender.com/webhooks/rest/webhook"

# ⚙️ Configuración de la página
st.set_page_config(page_title="Asistente Financiero", page_icon="💰")
st.title("💬 Chat con tu Asistente Financiero")

# ⏰ Función para mostrar la hora al estilo de WhatsApp
def hora_estilo_chat():
    lima_tz = pytz.timezone("America/Lima")
    ahora = datetime.now(lima_tz)
    return ahora.strftime("%I:%M %p").lstrip("0").replace("AM", "a. m.").replace("PM", "p. m.")

# 📦 Inicializar historial
if "messages" not in st.session_state:
    st.session_state.messages = []

# 🗂️ Mostrar historial con íconos personalizados y alineación
for msg in st.session_state.messages:
    es_usuario = msg["role"] == "user"
    hora = f"<div style='text-align: {'right' if es_usuario else 'left'}; font-size: 0.75rem; color: gray;'>{msg['hora']}</div>"

    if es_usuario:
        st.markdown(f"""
        <div style="display: flex; justify-content: flex-end; align-items: center; margin-bottom: 2px;">
            <div style="background-color: #daf0e9; padding: 8px 12px; border-radius: 12px; max-width: 70%; text-align: right;">
                {msg['content']}
            </div>
            <img src="https://cdn-icons-png.flaticon.com/512/4712/4712027.png" width="30" style="margin-left: 8px; border-radius: 50%;">
        </div>
        {hora}
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="display: flex; justify-content: flex-start; align-items: center; margin-bottom: 2px;">
            <img src="https://cdn-icons-png.flaticon.com/512/4712/4712017.png" width="30" style="margin-right: 8px; border-radius: 50%;">
            <div style="background-color: #ffffff; padding: 8px 12px; border-radius: 12px; max-width: 70%; text-align: left;">
                {msg['content']}
            </div>
        </div>
        {hora}
        """, unsafe_allow_html=True)

# 🔁 Función para enviar mensaje a Rasa
def enviar_a_rasa(mensaje):
    try:
        payload = {"sender": "usuario", "message": mensaje}
        response = requests.post(RASA_ENDPOINT, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        print("Respuesta de Rasa:", data)
        return [r["text"] for r in data if "text" in r]
    except Exception as e:
        print(f"Error al comunicarse con Rasa: {e}")
        return [f"❌ Error al comunicarse con el asistente: {e}"]

# 💬 Entrada del usuario
if mensaje_usuario := st.chat_input("Escribe algo..."):
    hora_actual = hora_estilo_chat()

    # Mostrar mensaje del usuario con ícono a la derecha
    st.markdown(f"""
    <div style="display: flex; justify-content: flex-end; align-items: center; margin-bottom: 2px;">
        <div style="background-color: #daf0e9; padding: 8px 12px; border-radius: 12px; max-width: 70%; text-align: right;">
            {mensaje_usuario}
        </div>
        <img src="https://cdn-icons-png.flaticon.com/512/4712/4712027.png" width="30" style="margin-left: 8px; border-radius: 50%;">
    </div>
    <div style="text-align: right; font-size: 0.75rem; color: gray;">{hora_actual}</div>
    """, unsafe_allow_html=True)

    st.session_state.messages.append({
        "role": "user",
        "content": mensaje_usuario,
        "hora": hora_actual
    })

    # Obtener respuesta del bot
    respuestas = enviar_a_rasa(mensaje_usuario)
    respuesta_completa = "\n\n".join(respuestas)
    hora_respuesta = hora_estilo_chat()

    # Mostrar respuesta del bot con ícono a la izquierda
    st.markdown(f"""
    <div style="display: flex; justify-content: flex-start; align-items: center; margin-bottom: 2px;">
        <img src="https://cdn-icons-png.flaticon.com/512/4712/4712017.png" width="30" style="margin-right: 8px; border-radius: 50%;">
        <div style="background-color: #ffffff; padding: 8px 12px; border-radius: 12px; max-width: 70%; text-align: left;">
            {respuesta_completa}
        </div>
    </div>
    <div style="text-align: left; font-size: 0.75rem; color: gray;">{hora_respuesta}</div>
    """, unsafe_allow_html=True)

    st.session_state.messages.append({
        "role": "assistant",
        "content": respuesta_completa,
        "hora": hora_respuesta
    })

# ✅ Botón flotante usando st.button con estilo embebido
from streamlit.components.v1 import html

# Crear columna flotante en posición absoluta con HTML y aplicar `st.button` ahí dentro
float_button = st.empty()

with float_button.container():
    st.markdown("""
    <style>
    div[data-testid="stHorizontalBlock"] {
        position: fixed;
        bottom: 90px;
        right: 32px;
        z-index: 9999;
        padding: 0px 12px;
        box-shadow: 2px 2px 8px rgba(0, 0, 0, 0.2);
    }
    div[data-testid="stHorizontalBlock"] button {
        background-color: #ff4b4b;
        color: white !important;
        font-weight: bold;
        border: none;
        border-radius: 20px;
        padding: 8px 16px;
        font-size: 14px;
        cursor: pointer;
        transition: background-color 0.3s ease;
    }
    div[data-testid="stHorizontalBlock"] button:hover {
        background-color: #e03e3e;
    }
    </style>
    """, unsafe_allow_html=True)

    if st.button("🧹 Limpiar"):
        st.session_state.messages = []
        st.experimental_rerun()
