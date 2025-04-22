# Usa una imagen base ligera con Python
FROM python:3.10-slim

# Crea y define el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia todos los archivos al contenedor
COPY . /app

# Instala pip y las dependencias necesarias
RUN pip install --upgrade pip && \
    pip install rasa && \
    pip install -r requirements.txt

# Expón el puerto por donde Rasa escuchará peticiones
EXPOSE 5055

# Comando por defecto al arrancar el contenedor
CMD ["rasa", "run", "actions", "--port", "5055"]
