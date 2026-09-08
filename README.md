# 🚀 RevealLess — Spoiler-Aware Social Platform

Plataforma social orientada al seguimiento y conversación sobre obras narrativas que adapta la visibilidad del contenido al progreso individual de cada usuario.

RevealLess nace como una evolución profunda de un proyecto previo de red social desarrollado con Django (`RedSocial_Django`), incorporando un nuevo dominio de negocio basado en una idea central:

> **PROGRESO → SPOILER → VISIBILIDAD**

El objetivo es permitir que los usuarios puedan compartir y descubrir contenido relacionado con una obra sin exponerse accidentalmente a acontecimientos que todavía no han visto o leído.

---

## 🧩 Overview

RevealLess combina las funcionalidades sociales de una red tradicional con un sistema de control de spoilers basado en el progreso narrativo de cada usuario.

Funcionalidades implementadas:

- 👤 Usuarios y perfiles
- 👥 Seguidores y relaciones sociales
- 📝 Publicaciones y comentarios
- ❤️ Reacciones
- 💬 Mensajería privada en tiempo real
- 🔔 Notificaciones en tiempo real
- 📺 Obras narrativas, con jerarquía de profundidad variable (temporadas, arcos, episodios...)
- ▶️ Seguimiento del progreso individual, con confirmación explícita para saltos grandes
- 🛡️ Motor de visibilidad anti-spoiler aplicado en feed, perfil y detalle de post
- 🤖 Asistente de IA (Anthropic Claude) para proponer clasificación narrativa
- 🔌 API REST (Django REST Framework) como base para las vistas React

Pendiente (ver Roadmap):

- ⚛️ Vistas React que consuman la API
- 🌐 Despliegue de la versión RevealLess en producción

La característica diferencial del proyecto es que la visibilidad de una publicación no depende únicamente de quién la ha publicado, sino también de **hasta dónde ha progresado el usuario dentro de la obra asociada**.

---

## 🎯 Problema

En las redes sociales y comunidades online relacionadas con series, películas, libros u otras obras narrativas, resulta habitual encontrar conversaciones que contienen información relevante de acontecimientos que otros usuarios todavía no han visto o leído.

Los sistemas tradicionales de etiquetado de spoilers dependen principalmente de que el usuario que publica el contenido lo clasifique correctamente y de que el receptor decida si quiere revelar ese contenido.

RevealLess plantea un enfoque diferente:

> **El sistema conoce el progreso narrativo del usuario y utiliza ese contexto para determinar qué contenido puede visualizar.**

De esta forma, dos usuarios pueden consultar la misma publicación y obtener resultados diferentes dependiendo de su progreso.

---

## 🧠 Concepto principal

El funcionamiento del sistema se basa en tres elementos:

```text
PROGRESO DEL USUARIO
        ↓
CONTEXTO NARRATIVO DE LA PUBLICACIÓN
        ↓
REGLA DE VISIBILIDAD
        ↓
CONTENIDO VISIBLE / BLOQUEADO
```

Regla nuclear del motor de visibilidad:

```text
progreso_usuario >= frontera_contenido → visible
```

Por ejemplo:

```text
Usuario A → S02E08
Usuario B → S02E03

Publicación → frontera S02E07

Usuario A → ✅ Puede verla
Usuario B → 🔒 Contenido bloqueado
```

Cuando el usuario B alcanza posteriormente el episodio 7, la publicación pasa a estar disponible automáticamente.

El autor de un contenido siempre puede ver lo que él mismo ha publicado, incluso si su frontera de spoiler está por delante de su propio progreso (por ejemplo, al comentar información externa como entrevistas o adelantos oficiales). Un usuario sin sesión iniciada no ve ningún contenido narrativo — solo un catálogo público de obras y estadísticas agregadas, sin información de trama.

---

## 🤖 Inteligencia Artificial

La IA (Anthropic Claude) se utiliza como **asistente de clasificación**, no como autoridad absoluta. La jerarquía de asignación de la frontera de spoiler de una publicación es:

```text
1. Usuario indica explícitamente
        ↓ (si no)
2. IA propone (con nivel de confianza)
        ↓ (si falla o confianza insuficiente)
3. Fallback: progreso del autor en el instante de creación (congelado)
```

Ante una publicación sin clasificación explícita, la IA analiza el texto junto con las unidades narrativas de la obra y propone cuál debería usarse como frontera, junto a un nivel de confianza (0–1). Si la confianza no alcanza el umbral mínimo, o la llamada a la API falla o hace timeout, el sistema no bloquea la publicación: aplica el fallback automáticamente.

Este enfoque combina automatización con una red de seguridad, evitando que un fallo de la IA deje contenido sin proteger.

---

## 🏗️ Arquitectura

RevealLess reutiliza la infraestructura social heredada de `RedSocial_Django` y añade una app de dominio propia (`narrative`) de la que dependen `posts` y `comments`:

```text
Cliente
   ↓
Django (vistas HTML + API REST)
   ↓
ASGI / Channels (chat, notificaciones en tiempo real)
   ↓
Redis
   ↓
WebSocket Consumers
   ↓
Base de datos
```

Flujo del dominio propio:

```text
Obra
   ↓
UnidadNarrativa (jerarquía autorreferenciada: parte/saga/arco/episodio...)
   ↓
ProgresoUsuario (por usuario y obra, declarativo, no puede retroceder)
   ↓
ClasificacionNarrativa (mixin abstracto: Post y Comment)
   ↓
Motor de visibilidad (Post.objects.visible_for / Comment.objects.visible_for)
```

---

## ⚙️ Stack Tecnológico

### Backend

- Python / Django 5.2
- Django ORM
- Django REST Framework (API para React)
- Django Channels + Daphne + channels_redis

### Frontend

- Django Templates
- JavaScript / Fetch API / WebSockets
- React (en desarrollo, consumiendo la API REST)

### Inteligencia Artificial

- Anthropic Claude (Haiku) para clasificación asistida de contenido
- Sistema de confianza y fallback automático

### Infraestructura

- Redis
- Fly.io
- SQLite (desarrollo) / PostgreSQL (a valorar en producción)

### Otros

- WhiteNoise, Pillow

---

## 🔌 Tiempo Real

RevealLess mantiene las capacidades de comunicación en tiempo real heredadas del proyecto base.

| Feature | Tecnología | Descripción |
| -------- | ---------- | ----------- |
| Chat | WebSockets | Mensajería privada en tiempo real |
| Notificaciones | WebSockets | Eventos y avisos en vivo |
| Reacciones | WebSockets | Actualización de reacciones |

**Nota:** `manage.py runserver` sirve WSGI puro y no atiende rutas `/ws/`; para probar tiempo real localmente hace falta levantar el servidor en modo ASGI (Daphne/uvicorn).

---

## ⚛️ Integración React

La API REST que consumirá React ya está construida y probada:

- `GET /narrative/api/feed/` — feed anti-spoiler, ya filtrado por el motor de visibilidad.
- `GET /narrative/api/progreso/<slug>/` — unidades narrativas de una obra + progreso actual del usuario.
- `POST /narrative/api/progreso/<slug>/` — actualiza el progreso (requiere `confirmado: true` si el salto es grande).

Autenticación por sesión (misma cookie que el resto de la app); las peticiones de escritura requieren el token CSRF estándar de Django, leído de la cookie `csrftoken` y enviado como cabecera `X-CSRFToken`.

Las vistas React que consumen estos endpoints están pendientes de implementación.

---

## 🧩 Funcionalidades principales

### 👤 Usuarios
Registro e inicio de sesión, perfiles, seguidores.

### 📚 Obras
`Obra` + `UnidadNarrativa` (jerarquía de profundidad variable), con portada opcional en ambos niveles.

### ▶️ Progreso
`ProgresoUsuario`: declarativo, no puede retroceder, exige confirmación explícita para saltos grandes (umbral configurable).

### 📝 Publicaciones
Creación asociada obligatoriamente a una obra; requiere progreso declarado antes de publicar; clasificación narrativa (explícita, IA o fallback); comentarios con herencia de frontera del post padre por defecto.

### 🛡️ Protección frente a spoilers
Motor de visibilidad aplicado en feed, perfil y detalle de post: `progreso_lector >= frontera_orden`.

### 🤖 Clasificación asistida por IA
Ver sección "Inteligencia Artificial" arriba.

---

## 🧪 Testing

El dominio anti-spoiler está cubierto por tests automatizados (`narrative/tests.py`, `posts/tests.py`, `comments/tests.py`):

```bash
python manage.py test narrative posts comments
```

Cobertura actual: recálculo de orden narrativo (incluyendo `orden_manual` y desempates), progreso (avance, no-retroceso, saltos grandes), clasificación narrativa y sus constraints, motor de visibilidad (post visible/bloqueado, autor viendo su propio contenido, usuario anónimo, herencia y bloqueo lateral de comentarios).

No cubierto todavía: llamadas reales a la API de IA (se prueban manualmente; un mock queda pendiente para no depender de cuota real en cada ejecución).

---

## 📦 Instalación local

```bash
git clone git@github.com:ASCiiLex/RevealLess.git

cd RevealLess

python -m venv venv

source venv/bin/activate
# Windows: venv\Scripts\activate

pip install -r requirements.txt
```

---

## ⚙️ Configuración

Variables de entorno usadas por el proyecto:

```bash
SECRET_KEY=your_secret_key
DJANGO_DEBUG=True
DATABASE_PATH=db.sqlite3          # opcional, por defecto usa db.sqlite3 en la raíz
REDIS_URL=redis://127.0.0.1:6379  # opcional en local; sin ella usa InMemoryChannelLayer
ANTHROPIC_API_KEY=sk-ant-...      # necesaria para que el asistente de IA funcione;
                                   # sin ella, cae automáticamente al fallback
```

Las credenciales y secretos reales no forman parte del repositorio (`.env` está en `.gitignore`).

---

## 🗄️ Base de datos

```bash
python manage.py migrate
python manage.py createsuperuser
```

---

## ▶️ Ejecutar entorno

```bash
python manage.py runserver
```

Cuando sean necesarias funcionalidades de tiempo real, Redis deberá estar disponible:

```bash
redis-server
```

---

## 🌐 Despliegue

El fork original (`RedSocial_Django`) ya cuenta con configuración para Fly.io (volumen persistente para SQLite, `SECURE_*` pendiente de revisión final). El despliegue de la versión RevealLess, incluyendo `ANTHROPIC_API_KEY` como secret de Fly, está pendiente.

---

## 📁 Estructura del proyecto

```text
RevealLess/
├── accounts/
├── posts/
├── comments/
├── likes/
├── follows/
├── feed/
├── profiles/
├── notifications/
├── messages_app/
├── saved_posts/
├── narrative/          # dominio propio: Obra, UnidadNarrativa, ProgresoUsuario,
│                        # ClasificacionNarrativa, motor de visibilidad, API REST, IA
├── media/
├── static/
├── core/
├── manage.py
└── requirements.txt
```

---

## 🔮 Roadmap

### PFM — V1

- [x] Sistema de usuarios y perfiles
- [x] Obras, unidades narrativas y jerarquía
- [x] Seguimiento de progreso (con confirmación de saltos grandes)
- [x] Publicaciones asociadas a contexto narrativo
- [x] Motor de visibilidad anti-spoiler
- [x] Clasificación asistida mediante IA
- [x] Tests del dominio anti-spoiler
- [x] Base de API REST para React
- [ ] Integración React (vistas de feed y progreso)
- [ ] Seguridad de producción (`SECURE_*`, revisión final)
- [ ] Despliegue de la versión RevealLess
- [ ] Documentación técnica (memoria del proyecto) y vídeo

### V2 / Futuras evoluciones

- Clasificación narrativa más avanzada (`FamiliaNarrativa` extendida)
- Clasificación propia de comentarios vía interfaz (hoy solo heredan del post por defecto)
- Sistemas de recomendación
- RAG, agentes inteligentes
- Más tipos de obras (libro, manga)
- Notificaciones push
- Aplicación móvil
- Gamificación

Estas funcionalidades quedan fuera del alcance del PFM.

---

## 📄 Proyecto Final de Máster

RevealLess constituye el Proyecto Final de Máster del Máster en Desarrollo Full Stack.

El proyecto parte de la experiencia adquirida durante el desarrollo de `RedSocial_Django` y plantea una evolución sustancial hacia un producto con un dominio de negocio propio.

El objetivo no es únicamente ampliar una aplicación existente, sino demostrar la capacidad para:

- Analizar un problema
- Diseñar una solución
- Definir una arquitectura
- Implementar un backend Django
- Integrar React
- Aplicar inteligencia artificial
- Diseñar reglas de negocio
- Implementar seguridad y validaciones
- Realizar testing
- Desplegar una aplicación funcional
- Documentar y defender las decisiones técnicas adoptadas

---

## 📄 Licencia

Proyecto personal con fines educativos y de portfolio.

---

## 👨‍💻 Autor

Desarrollado por **Álex**

Proyecto orientado a demostrar competencias de desarrollo Full Stack mediante Django, React, tiempo real e inteligencia artificial.