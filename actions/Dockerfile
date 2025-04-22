FROM rasa/rasa-sdk:3.5.11

WORKDIR /app

# Copia tus archivos de acciones personalizados
COPY . /app

# Instala tus dependencias adicionales
RUN pip install -r requirements.txt

EXPOSE 5055

CMD ["start", "--actions", "actions", "--port", "5055"]
