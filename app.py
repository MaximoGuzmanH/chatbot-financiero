import streamlit as st
import requests

# 🌍 URL del túnel Cloudflare apuntando al servidor Rasa
RASA_ENDPOINT = "https://manufactured-antonio-palm-golden.trycloudflare.com/webhooks/rest/webhook"

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
        return [r["text"] for r in data if "text" in r]
    except Exception as e:
        return [f"❌ Error al comunicarse con el asistente: {e}"]

# Entrada del usuario
if mensaje_usuario := st.chat_input("Escribe algo..."):
    # Mostrar mensaje del usuario
    st.chat_message("user").markdown(mensaje_usuario)
    st.session_state.messages.append({"role": "user", "content": mensaje_usuario})

    # Obtener respuesta de Rasa
    respuestas = enviar_a_rasa(mensaje_usuario)
    for r in respuestas:
        st.chat_message("assistant").markdown(r)
        st.session_state.messages.append({"role": "assistant", "content": r})
