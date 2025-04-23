import streamlit as st
import requests
from datetime import datetime

# 🔗 Configuración del endpoint
RASA_ENDPOINT = "https://chatbot-financiero.onrender.com/webhooks/rest/webhook"

# ⚙️ Configuración de la página
st.set_page_config(page_title="Asistente Financiero", page_icon="💰")
st.title("💬 Chat con tu Asistente Financiero")

# ⏰ Función para mostrar la hora al estilo de WhatsApp
def hora_estilo_chat():
    return datetime.now().strftime("%I:%M %p").lstrip("0").replace("AM", "a. m.").replace("PM", "p. m.")

# 📦 Inicializar historial
if "messages" not in st.session_state:
    st.session_state.messages = []

# 🗂️ Mostrar historial previo con hora
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        st.markdown(f"<sub>{msg['hora']}</sub>", unsafe_allow_html=True)

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

    # Mostrar mensaje del usuario
    with st.chat_message("user"):
        st.markdown(mensaje_usuario)
        st.markdown(f"<sub>{hora_actual}</sub>", unsafe_allow_html=True)

    st.session_state.messages.append({
        "role": "user",
        "content": mensaje_usuario,
        "hora": hora_actual
    })

    # Obtener respuesta del bot
    respuestas = enviar_a_rasa(mensaje_usuario)
    respuesta_completa = "\n\n".join(respuestas)
    hora_respuesta = hora_estilo_chat()

    with st.chat_message("assistant"):
        st.markdown(respuesta_completa, unsafe_allow_html=True)
        st.markdown(f"<sub>{hora_respuesta}</sub>", unsafe_allow_html=True)

    st.session_state.messages.append({
        "role": "assistant",
        "content": respuesta_completa,
        "hora": hora_respuesta
    })

    # 🧭 Scroll automático
    st.markdown("""
        <script>
            window.scrollTo(0, document.body.scrollHeight);
        </script>
    """, unsafe_allow_html=True)