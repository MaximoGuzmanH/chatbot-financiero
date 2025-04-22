# Usa imagen oficial de Rasa, ya trae todo configurado
FROM rasa/rasa:3.6.10

# Copiar el contenido del proyecto al contenedor
COPY . /app
WORKDIR /app

# Exponer el puerto por defecto
EXPOSE 5005

# Comando de arranque
CMD ["rasa", "run", "--enable-api", "--cors", "*", "--debug", "--model", "/app/models/model.tar.gz"]