FROM rasa/rasa-sdk:3.6.2

USER root

WORKDIR /app

COPY . /app

# Instalar pip actualizado y requerimientos como root
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Regresar al usuario sin privilegios
USER 1001

EXPOSE 5055

CMD ["start", "--actions", "actions", "--port", "5055"]
