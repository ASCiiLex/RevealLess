FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencias sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Dependencias Python
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copiar proyecto
COPY . .

# Static
RUN python manage.py collectstatic --noinput

# Puerto
EXPOSE 8080

# 🔥 ASGI (Daphne + Channels)
CMD ["daphne", "-b", "0.0.0.0", "-p", "8080", "core.asgi:application"]