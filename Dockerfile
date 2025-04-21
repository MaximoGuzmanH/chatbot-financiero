# Imagen base con Python 3.10 y pip
FROM python:3.10

# Instala Rasa y demás dependencias
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copia todo el proyecto
COPY . /app
WORKDIR /app

# Exponer puerto de la API
EXPOSE 5005

# Comando para correr Rasa en modo servidor API
CMD ["rasa", "run", "--enable-api", "--cors", "*", "--debug"]
