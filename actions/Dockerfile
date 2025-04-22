FROM python:3.8-slim

WORKDIR /app

COPY . /app

# Actualiza pip y configura entorno base
RUN apt-get update && apt-get install -y gcc

RUN pip install --upgrade pip

# Instala rasa y rasa-sdk directamente desde PyPI (versión válida y disponible)
RUN pip install rasa==3.5.11
RUN pip install rasa-sdk==3.5.11

# Instala otras dependencias
RUN pip install -r requirements.txt

EXPOSE 5055

CMD ["rasa", "run", "actions", "--port", "5055"]
