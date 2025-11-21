FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей
RUN pip install --user flask

# Копирование приложения
COPY app.py .

EXPOSE 5000

CMD ["python", "app.py"]