FROM python:3.11-slim AS base

# Instalar dependencias
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copiar el código fuente
COPY . /app
WORKDIR /app

# Establecer permisos de ejecución y punto de entrada
RUN chmod +x project/entrypoint.sh

# Environment variables
ENV PORT=8501

ENTRYPOINT ["bash", "project/entrypoint.sh"]
