# Imagen base con Python 3.10
FROM python:3.10

# Copiar archivo de dependencias
COPY requirements.txt ./

# Instalar dependencias y limpiar caché
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    rm -rf ~/.cache/pip

# Copiar el contenido del proyecto al contenedor
COPY . /app
WORKDIR /app

# Exponer el puerto en el que se ejecuta Rasa por defecto
EXPOSE 5005

# Comando por defecto: iniciar el servidor de Rasa con API y CORS habilitado
CMD ["rasa", "run", "--enable-api", "--cors", "*", "--debug", "--model", "models/model.tar.gz"]
