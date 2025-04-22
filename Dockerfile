# Imagen base
FROM python:3.10-slim

# Crear carpeta de trabajo
WORKDIR /app

# Copiar dependencias primero (mejor caché)
COPY requirements.txt .

# Instalar dependencias
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copiar todo el proyecto
COPY . .

# Exponer puerto 5005 (por defecto en Rasa)
EXPOSE 5005

# Comando de inicio
ENTRYPOINT ["python"]
CMD ["-m", "rasa", "run", "--enable-api", "--cors", "*", "--debug", "--model", "models/model.tar.gz"]
