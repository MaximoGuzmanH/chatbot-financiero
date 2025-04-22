# Base compatible con Rasa
FROM python:3.10

# Crear carpeta de trabajo
WORKDIR /app

# Copiar primero requirements.txt para aprovechar caché
COPY requirements-render.txt ./requirements.txt

# Instalar dependencias del sistema necesarias para Rasa
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    graphviz \
    git \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copiar el resto del proyecto
COPY . .

# DEBUG: listar contenido del directorio models (verificación)
RUN ls -lh models/

# Exponer el puerto de Rasa
EXPOSE 5005

# Comando de inicio del servicio Rasa (forma correcta)
CMD ["rasa", "run", "--enable-api", "--cors", "*", "--debug", "--model", "models/model.tar.gz"]