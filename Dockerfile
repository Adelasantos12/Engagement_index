FROM python:3.11-slim AS base

# Copiar wheelhouse y requerimientos
COPY wheels/ /wheelhouse/
COPY requirements_lock.txt /tmp/requirements_lock.txt

# Instalar dependencias sin conexión
RUN pip install --no-index --find-links=/wheelhouse -r /tmp/requirements_lock.txt

# Copiar el código fuente
COPY . /app
WORKDIR /app

# Establecer permisos de ejecución y punto de entrada
RUN chmod +x project/entrypoint.sh
ENTRYPOINT ["bash", "project/entrypoint.sh"]
