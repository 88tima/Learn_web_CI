FROM python:3.11-slim

WORKDIR /app

COPY app.py .
RUN pip install flask prometheus_client psutil

# Создаём файл лога заранее (чтобы Promtail мог его отслеживать)
RUN touch /app/app.log

EXPOSE 5000

CMD ["python", "app.py"]
