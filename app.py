import streamlit as st
import requests

RASA_ENDPOINT = "https://chatbot-financiero.onrender.com/webhooks/rest/webhook"

# Configuración de la página
st.set_page_config(page_title="Asistente Financiero", page_icon="💰")


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
    with st.chat_message("user"):
        st.markdown(mensaje_usuario)
    st.session_state.messages.append({"role": "user", "content": mensaje_usuario})

    # Obtener respuesta de Rasa
    respuestas = enviar_a_rasa(mensaje_usuario)
    for r in respuestas:
        with st.chat_message("assistant"):
            st.markdown(r, unsafe_allow_html=True)
        st.session_state.messages.append({"role": "assistant", "content": r})

    # Scroll automático al final
    st.markdown("""
        <script>
            window.scrollTo(0, document.body.scrollHeight);
        </script>
    """, unsafe_allow_html=True)
