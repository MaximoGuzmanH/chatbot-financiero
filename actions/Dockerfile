# /actions/Dockerfile

FROM python:3.10

# Establece el directorio de trabajo
WORKDIR /app

# Copia solo los archivos necesarios de la carpeta actions
COPY requirements-actions.txt ./
COPY actions.py ./
COPY alertas_io.py ./
COPY transacciones_io.py ./

# Instala las dependencias necesarias
RUN pip install --upgrade pip && \
    pip install rasa==3.6.10 && \
    pip install -r requirements-actions.txt

# Puerto de Rasa Actions
EXPOSE 5055

# Comando para ejecutar el servidor de acciones
CMD ["rasa", "run", "actions"]
