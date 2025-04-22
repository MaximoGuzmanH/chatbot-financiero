# Base compatible con Rasa
FROM python:3.10

# Crear carpeta de trabajo
WORKDIR /app

# Copiar primero requirements.txt para aprovechar la caché de Docker
COPY requirements.txt .

# Instalar dependencias del sistema necesarias para Rasa
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    graphviz \
    git \
    && pip install --upgrade pip \
    && pip install -r requirements.txt \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copiar el resto del proyecto
COPY . .

# Exponer el puerto de Rasa
EXPOSE 5005

# Comando de inicio del servicio Rasa
ENTRYPOINT ["python"]
CMD ["-m", "rasa", "run", "--enable-api", "--cors", "*", "--debug", "--model", "models/model.tar.gz"]