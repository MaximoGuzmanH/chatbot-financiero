FROM python:3.8-slim

WORKDIR /app

COPY . /app

# Instala pip actualizado y dependencias
RUN pip install --upgrade pip && \
    pip install rasa==3.5.11 rasa-sdk==3.5.11 && \
    pip install -r requirements.txt

EXPOSE 5055

CMD ["rasa", "run", "actions", "--port", "5055"]
