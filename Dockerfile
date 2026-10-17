# Etapa 1: compila el frontend (Vite) en static/frontend/dist
FROM node:22-slim AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Etapa 2: Django servido por Daphne (ASGI)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
COPY --from=frontend /app/static/frontend/dist ./static/frontend/dist

# collectstatic no usa la BD ni secretos: la clave solo permite cargar settings.
RUN SECRET_KEY=solo-para-build DJANGO_DEBUG=False python manage.py collectstatic --noinput

RUN useradd --create-home --uid 1000 app
USER app

# Render fija PORT (10000 por defecto). Las migraciones van en el preDeployCommand de render.yaml.
CMD ["sh", "-c", "exec daphne -b 0.0.0.0 -p ${PORT:-8000} core.asgi:application"]