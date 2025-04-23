import streamlit as st
import requests

RASA_ENDPOINT = "https://chatbot-financiero.onrender.com/webhooks/rest/webhook"

# Configuración de la página
st.set_page_config(page_title="Asistente Financiero", page_icon="💰")

st.markdown("""
    <style>
    .stChatMessage.user {
        text-align: right !important;
        background-color: #DCF8C6;
        border-radius: 15px 15px 0px 15px;
        padding: 10px 15px;
        margin: 10px 40px 10px auto;
        display: inline-block;
        max-width: 70%;
        word-wrap: break-word;
        font-family: "Segoe UI", "Helvetica Neue", sans-serif;
        font-size: 16px;
        line-height: 1.4;
    }

    .stChatMessage.assistant {
        text-align: left !important;
        background-color: #F1F0F0;
        border-radius: 15px 15px 15px 0px;
        padding: 10px 15px;
        margin: 10px auto 10px 40px;
        display: inline-block;
        max-width: 70%;
        word-wrap: break-word;
        font-family: "Segoe UI", "Helvetica Neue", sans-serif;
        font-size: 16px;
        line-height: 1.4;
    }

    .stChatMessage {
        padding: 0 !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("💬 Chat con tu Asistente Financiero")

# Inicializar historial de chat en sesión
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar historial previo
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Función para enviar mensajes al servidor de Rasa
def enviar_a_rasa(mensaje):
    try:
        payload = {"sender": "usuario", "message": mensaje}
        response = requests.post(RASA_ENDPOINT, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        print("Respuesta de Rasa:", data)  # <--- AÑADE ESTO
        return [r["text"] for r in data if "text" in r]
    except Exception as e:
        print(f"Error al comunicarse con Rasa: {e}")  # <--- Y ESTO
        return [f"❌ Error al comunicarse con el asistente: {e}"]

# Entrada del usuario
if mensaje_usuario := st.chat_input("Escribe algo..."):
    # Mostrar mensaje del usuario
    st.markdown(f'<div class="stChatMessage user">{mensaje_usuario}</div>', unsafe_allow_html=True)
    st.session_state.messages.append({"role": "user", "content": mensaje_usuario})

    # Obtener respuesta de Rasa
    respuestas = enviar_a_rasa(mensaje_usuario)
    for r in respuestas:
        st.markdown(f'<div class="stChatMessage assistant">{r}</div>', unsafe_allow_html=True)
        st.session_state.messages.append({"role": "assistant", "content": r})

    # Scroll automático al final
    st.markdown("""
        <script>
            window.scrollTo(0, document.body.scrollHeight);
        </script>
    """, unsafe_allow_html=True)
