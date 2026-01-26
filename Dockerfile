FROM python:3.11-slim

WORKDIR /app

COPY app.py .
RUN pip install flask prometheus_client psutil

# Создаём директорию для логов
RUN mkdir -p /var/log/app

EXPOSE 5000

# Пишем логи в файл И stdout
CMD ["sh", "-c", "python app.py 2>&1 | tee -a /var/log/app/app.log"]

