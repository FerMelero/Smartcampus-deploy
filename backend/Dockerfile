FROM python:3.12-slim

# Evita .pyc y buffer en logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /code

# Primero requirements: aprovecha la cache de capas si el codigo cambia pero las dependencias no
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Usuario no root
RUN useradd --create-home appuser && chown -R appuser /code
USER appuser

EXPOSE 8000

# La conexion a la base de datos se configura con DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
