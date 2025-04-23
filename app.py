import streamlit as st
import requests
from datetime import datetime
import pytz

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

# 🗂️ Mostrar historial previo con hora
for msg in st.session_state.messages:
    alineacion = "left" if msg["role"] == "assistant" else "right"
    estilo = f"text-align: {alineacion}; background-color: #f0f2f6; padding: 8px 12px; border-radius: 12px; margin: 4px 0;"
    hora = f"<div style='text-align:{alineacion}; font-size:0.75rem; color:gray'>{msg['hora']}</div>"

    with st.chat_message(msg["role"]):
        st.markdown(f"<div style='{estilo}'>{msg['content']}</div>", unsafe_allow_html=True)
        st.markdown(hora, unsafe_allow_html=True)

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

    # Mostrar mensaje del usuario alineado a la derecha
    with st.chat_message("user"):
        st.markdown(
            f"<div style='text-align: right; background-color: #daf0e9; padding: 8px 12px; border-radius: 12px; margin: 4px 0;'>{mensaje_usuario}</div>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<div style='text-align:right; font-size:0.75rem; color:gray'>{hora_actual}</div>",
            unsafe_allow_html=True
        )

    st.session_state.messages.append({
        "role": "user",
        "content": mensaje_usuario,
        "hora": hora_actual
    })

    # Obtener respuesta del bot
    respuestas = enviar_a_rasa(mensaje_usuario)
    respuesta_completa = "\n\n".join(respuestas)
    hora_respuesta = hora_estilo_chat()

    # Mostrar respuesta del bot alineada a la izquierda
    with st.chat_message("assistant"):
        st.markdown(
            f"<div style='text-align: left; background-color: #ffffff; padding: 8px 12px; border-radius: 12px; margin: 4px 0;'>{respuesta_completa}</div>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<div style='text-align:left; font-size:0.75rem; color:gray'>{hora_respuesta}</div>",
            unsafe_allow_html=True
        )

    st.session_state.messages.append({
        "role": "assistant",
        "content": respuesta_completa,
        "hora": hora_respuesta
    })

# 🧹 Botón flotante para limpiar conversación (siempre visible)
st.markdown("""
    <style>
    .floating-button {
        position: fixed;
        bottom: 90px;
        right: 20px;
        background-color: #ff4b4b;
        color: white;
        border: none;
        border-radius: 20px;
        padding: 10px 16px;
        font-size: 14px;
        font-weight: bold;
        cursor: pointer;
        box-shadow: 2px 2px 8px rgba(0, 0, 0, 0.2);
        z-index: 100;
        transition: background-color 0.3s ease;
    }
    .floating-button:hover {
        background-color: #e03e3e;
    }
    </style>
    <form action="" method="post">
        <button class="floating-button" name="clear" type="submit">🧹 Limpiar</button>
    </form>
""", unsafe_allow_html=True)

if st.session_state.get("clear"):
    st.session_state.messages = []
    st.experimental_rerun()