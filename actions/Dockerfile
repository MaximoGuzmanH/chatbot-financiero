FROM rasa/rasa-sdk:3.0.0

WORKDIR /app

COPY . /app

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

EXPOSE 5055

CMD ["start", "--actions", "actions", "--port", "5055"]
