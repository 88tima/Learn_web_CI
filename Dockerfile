FROM python:3.11-slim

WORKDIR /app

COPY app.py .
RUN pip install flask prometheus_client psutil

# Создаём директорию для логов
RUN mkdir -p /var/log/app

EXPOSE 5000

CMD ["python", "app.py"]
