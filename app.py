from flask import Flask, request
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST
import psutil
import logging
import os

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),  # Логи будут писаться в файл app.log
        logging.StreamHandler()          # Также в консоль
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# --- Метрики Prometheus ---
# Счётчик обработанных запросов (бизнес-метрика)
REQUEST_COUNT = Counter('flask_request_count', 'Total number of requests processed')

# Счётчик успешных/неудачных преобразований
TRANSFORM_SUCCESS = Counter('flask_transform_success', 'Number of successful transformations')
TRANSFORM_FAILED = Counter('flask_transform_failed', 'Number of failed transformations')

# Гейджи для системных метрик
CPU_USAGE = Gauge('system_cpu_percent', 'Current CPU usage percent')
RAM_USAGE = Gauge('system_memory_percent', 'Current RAM usage percent')
DISK_USAGE = Gauge('system_disk_percent', 'Current disk usage percent')

# Healthcheck метрика (1 = healthy, 0 = unhealthy)
HEALTHCHECK = Gauge('application_health', 'Application health status')

# --- Функция для обновления системных метрик ---
def update_system_metrics():
    CPU_USAGE.set(psutil.cpu_percent())
    RAM_USAGE.set(psutil.virtual_memory().percent)
    DISK_USAGE.set(psutil.disk_usage('/').percent)

# --- Эндпоинт для метрик Prometheus ---
@app.route('/metrics')
def metrics():
    update_system_metrics()  # Обновляем метрики перед отправкой
    HEALTHCHECK.set(1)       # Приложение живо
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

# --- Эндпоинт для healthcheck ---
@app.route('/health')
def health():
    try:
        # Простой healthcheck: если дошли сюда — приложение работает
        update_system_metrics()
        HEALTHCHECK.set(1)
        return "OK", 200
    except Exception as e:
        HEALTHCHECK.set(0)
        logger.error(f"Healthcheck failed: {e}")
        return "ERROR", 500

# --- Основной HTML шаблон ---
html_page = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Конвертер текста</title>
<style>
body {{
font-family: Arial, sans-serif;
background: {bg_color};
color: {text_color};
display: flex;
justify-content: center;
margin-top: 50px;
transition: 0.3s;
}}
.container {{
background: {container_bg};
padding: 25px 30px;
border-radius: 12px;
box-shadow: 0 4px 20px rgba(0,0,0,0.15);
width: 420px;
opacity: 0;
animation: fadeIn 0.5s forwards;
}}
@keyframes fadeIn {{
from {{ opacity: 0; transform: translateY(10px); }}
to {{ opacity: 1; transform: translateY(0); }}
}}
h2 {{
text-align: center;
margin-bottom: 20px;
}}
textarea {{
width: 100%;
border-radius: 8px;
border: 1px solid #888;
padding: 10px;
font-size: 15px;
resize: vertical;
outline: none;
background: {input_bg};
color: {text_color};
transition: 0.3s;
}}
select {{
width: 100%;
padding: 10px;
border-radius: 8px;
border: 1px solid #888;
background: {input_bg};
color: {text_color};
margin-top: 10px;
outline: none;
}}
button {{
margin-top: 15px;
width: 100%;
background: #4a90e2;
color: white;
font-size: 16px;
padding: 10px;
border: none;
border-radius: 8px;
cursor: pointer;
transition: 0.2s;
}}
button:hover {{
background: #3f7ac0;
}}
.result-box {{
margin-top: 20px;
padding: 12px;
min-height: 50px;
border-radius: 8px;
border: 1px solid #555;
background: {input_bg};
white-space: pre-wrap;
}}
.theme-toggle {{
margin-top: 10px;
text-align: center;
font-size: 14px;
cursor: pointer;
color: #4a90e2;
}}
</style>
</head>
<body>
<div class="container">
<h2>Конвертер текста</h2>
<form method="POST">
<textarea name="text" rows="6" placeholder="Введите текст...">{text}</textarea>
<select name="mode">
<option value="upper" {sel_upper}>Верхний регистр</option>
<option value="lower" {sel_lower}>Нижний регистр</option>
<option value="invert" {sel_invert}>Инверсия регистра</option>
<option value="count" {sel_count}>Количество символов</option>
</select>
<input type="hidden" name="theme" value="{theme}">
<button type="submit">Преобразовать</button>
</form>
<div class="theme-toggle" onclick="toggleTheme()">Сменить тему</div>
<h3>Результат:</h3>
<div class="result-box">{result}</div>
</div>
<script>
function toggleTheme() {{
const params = new URLSearchParams(window.location.search);
const current = "{theme}";
const next = current === "light" ? "dark" : "light";
params.set("theme", next);
window.location.search = params.toString();
}}
</script>
</body>
</html>
"""

def transform(text, mode):
    if mode == "upper":
        return text.upper()
    if mode == "lower":
        return text.lower()
    if mode == "invert":
        return "".join(ch.upper() if ch.islower() else ch.lower() for ch in text)
    if mode == "count":
        return f"Количество символов: {len(text)}"
    return text

@app.route("/", methods=["GET", "POST"])
def index():
    text = ""
    result = ""
    mode = "upper"
    theme = request.values.get("theme", "light")
    if theme == "light":
        colors = {
            "bg_color": "#f2f4f7",
            "text_color": "#000",
            "container_bg": "#fff",
            "input_bg": "#fafafa"
        }
    else:
        colors = {
            "bg_color": "#1e1e1e",
            "text_color": "#eee",
            "container_bg": "#2a2a2a",
            "input_bg": "#333"
        }

    if request.method == "POST":
        text = request.form.get("text", "")
        mode = request.form.get("mode", "upper")

        # Инкрементируем счётчик запросов
        REQUEST_COUNT.inc()

        try:
            result = transform(text, mode)
            TRANSFORM_SUCCESS.inc()
            logger.info(f"Successfully transformed text: '{text[:50]}...' with mode '{mode}'")
        except Exception as e:
            result = f"Ошибка: {str(e)}"
            TRANSFORM_FAILED.inc()
            logger.error(f"Transformation failed for text: '{text[:50]}...' with mode '{mode}'. Error: {e}")

    return html_page.format(
        result=result,
        text=text,
        theme=theme,
        sel_upper="selected" if mode == "upper" else "",
        sel_lower="selected" if mode == "lower" else "",
        sel_invert="selected" if mode == "invert" else "",
        sel_count="selected" if mode == "count" else "",
        **colors
    )

if __name__ == "__main__":
    # Запускаем сервер
    app.run(host='0.0.0.0', port=5000, debug=True)
