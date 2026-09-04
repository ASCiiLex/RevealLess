# 🚀 RevealLess — Spoiler-Aware Social Platform

Plataforma social orientada al seguimiento y conversación sobre obras narrativas que adapta la visibilidad del contenido al progreso individual de cada usuario.

RevealLess nace como una evolución profunda de un proyecto previo de red social desarrollado con Django, incorporando un nuevo dominio de negocio basado en una idea central:

> **PROGRESO → SPOILER → VISIBILIDAD**

El objetivo es permitir que los usuarios puedan compartir y descubrir contenido relacionado con una obra sin exponerse accidentalmente a acontecimientos que todavía no han visto o leído.

---

## 🧩 Overview

RevealLess combina las funcionalidades sociales de una red tradicional con un sistema de control de spoilers basado en el progreso narrativo de cada usuario.

Entre las funcionalidades previstas se encuentran:

- 👤 Usuarios y perfiles
- 👥 Seguidores y relaciones sociales
- 📝 Publicaciones y comentarios
- ❤️ Reacciones
- 💬 Mensajería privada en tiempo real
- 🔔 Notificaciones en tiempo real
- 📺 Obras narrativas y temporadas
- ▶️ Seguimiento del progreso individual
- 🛡️ Control automático de visibilidad según progreso
- 🤖 Inteligencia artificial como asistente de clasificación de contenido
- ⚛️ Integración de React en las vistas principales del producto

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

Por ejemplo:

```text
Usuario A → S02E08
Usuario B → S02E03

Publicación → S02E07

Usuario A → ✅ Puede verla
Usuario B → 🔒 Contenido bloqueado
```

Cuando el usuario B alcanza posteriormente el episodio 7, la publicación pasa a estar disponible.

---

## 🤖 Inteligencia Artificial

La inteligencia artificial se utilizará como **asistente de clasificación**, no como autoridad absoluta.

Ante una nueva publicación, el sistema podrá analizar su contenido y proponer información como:

- Obra a la que pertenece
- Temporada
- Episodio o posición narrativa
- Nivel de spoiler
- Elementos narrativos detectados
- Nivel de confianza de la clasificación

El usuario podrá revisar y corregir la clasificación cuando sea necesario.

Este enfoque permite combinar automatización con control humano y evitar que una clasificación incorrecta determine de forma irreversible la visibilidad del contenido.

---

## 🏗️ Arquitectura

La arquitectura definitiva del proyecto se establecerá durante la fase de diseño y análisis técnico.

Como punto de partida, RevealLess reutiliza parte de la infraestructura desarrollada en el proyecto RedSocial_Django:

```text
Cliente
   ↓
Django
   ↓
ASGI / Channels
   ↓
Redis
   ↓
WebSocket Consumers
   ↓
Base de datos
```

La nueva arquitectura incorporará progresivamente los componentes específicos del dominio RevealLess, especialmente:

```text
Obras
   ↓
Progreso del usuario
   ↓
Contexto narrativo
   ↓
Clasificación de publicaciones
   ↓
Motor de visibilidad
```

La arquitectura final será documentada una vez concluida la fase de análisis y diseño.

---

## ⚙️ Stack Tecnológico

### Backend

- Python
- Django
- Django ORM
- Django Channels
- Daphne
- channels_redis

### Frontend

- Django Templates
- JavaScript
- Fetch API
- WebSockets
- React

### Inteligencia Artificial

- Servicio de IA para clasificación asistida de contenido
- Sistema de confianza y revisión

### Infraestructura

- Redis
- Docker
- Fly.io
- PostgreSQL / SQLite según entorno

### Otros

- WhiteNoise
- Pillow

---

## 🔌 Tiempo Real

RevealLess mantiene las capacidades de comunicación en tiempo real heredadas del proyecto base.

Entre las funcionalidades previstas:

| Feature | Tecnología | Descripción |
| -------- | ---------- | ----------- |
| Chat | WebSockets | Mensajería privada en tiempo real |
| Notificaciones | WebSockets | Eventos y avisos en vivo |
| Reacciones | WebSockets | Actualización de reacciones |
| Contadores | WebSockets / JS | Sincronización dinámica |

El objetivo es mantener un enfoque orientado a eventos y evitar el polling innecesario.

---

## ⚛️ Integración React

El proyecto incorporará React en las partes del sistema donde aporte mayor valor y permita demostrar la integración entre frontend y backend.

Las primeras vistas candidatas son:

- Feed personalizado con control de spoilers
- Gestión del progreso del usuario

Estas vistas consumirán datos reales proporcionados por el backend Django.

La integración no pretende sustituir innecesariamente toda la interfaz existente, sino utilizar React de forma estratégica dentro de la arquitectura del proyecto.

---

## 🧩 Funcionalidades principales

### 👤 Usuarios

- Registro e inicio de sesión
- Perfiles
- Seguidores
- Relaciones sociales

### 📚 Obras

- Obras narrativas
- Temporadas
- Episodios
- Información contextual

### ▶️ Progreso

- Registro del progreso individual
- Actualización del progreso
- Asociación entre usuario y obra

### 📝 Publicaciones

- Creación de publicaciones
- Asociación con una obra
- Clasificación narrativa
- Comentarios
- Reacciones

### 🛡️ Protección frente a spoilers

El sistema comparará:

```text
Progreso del usuario
        +
Contexto narrativo de la publicación
        ↓
Visibilidad permitida
```

Una publicación podrá mostrarse, ocultarse o bloquearse dependiendo del progreso del usuario.

### 🤖 Clasificación asistida por IA

La IA podrá proponer la clasificación narrativa de una publicación y su nivel de confianza.

Las clasificaciones podrán ser revisadas o corregidas antes de determinar definitivamente su visibilidad.

---

## 🧪 Testing

El sistema deberá incluir pruebas orientadas especialmente a las reglas de negocio relacionadas con spoilers y visibilidad.

Ejemplos:

```text
Usuario → E03
Post    → E07
Resultado → 🔒 Bloqueado

Usuario → E08
Post    → E07
Resultado → ✅ Visible

Usuario → E03
Post    → E03
Resultado → ✅ Visible

Usuario → E03
Post    → E04
Resultado → 🔒 Bloqueado
```

También se contemplarán escenarios de:

- Clasificación incorrecta
- Baja confianza de IA
- Fallos del servicio de IA
- Corrección manual de una clasificación
- Cambios en el progreso del usuario

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

Las variables de entorno necesarias se definirán durante la fase de configuración del proyecto.

Ejemplo:

```bash
SECRET_KEY=your_secret_key
DEBUG=True
REDIS_URL=redis://127.0.0.1:6379
```

Las credenciales y secretos reales no forman parte del repositorio.

---

## 🗄️ Base de datos

```bash
python manage.py migrate
```

---

## ▶️ Ejecutar entorno

```bash
python manage.py runserver
```

Cuando sean necesarias funcionalidades de tiempo real, Redis deberá estar disponible.

```bash
redis-server
```

---

## 🐳 Docker

El proyecto incluye configuración Docker heredada del proyecto base y será adaptada progresivamente a las necesidades específicas de RevealLess.

---

## 🌐 Despliegue

El proyecto está preparado para mantener una estrategia de despliegue mediante contenedores.

El entorno de producción definitivo y sus servicios asociados se establecerán durante la fase de arquitectura y despliegue del PFM.

---

## 📁 Estructura del proyecto

La estructura actual parte del proyecto RedSocial_Django y será reorganizada durante la evolución del sistema.

Entre los componentes iniciales se encuentran:

```text
RevealLess/
├── accounts/
├── posts/
├── comments/
├── likes/
├── follows/
├── notifications/
├── messages_app/
├── media/
├── static/
├── templates/
├── core/
├── manage.py
└── requirements.txt
```

La estructura definitiva reflejará la separación entre funcionalidades sociales heredadas y el nuevo dominio RevealLess.

---

## 🔮 Roadmap

### PFM — V1

- Sistema de usuarios y perfiles
- Obras, temporadas y episodios
- Seguimiento de progreso
- Publicaciones asociadas a contexto narrativo
- Motor de visibilidad anti-spoiler
- Clasificación asistida mediante IA
- Integración React
- Testing
- Seguridad
- Despliegue
- Documentación técnica

### V2 / Futuras evoluciones

Posibles líneas de evolución:

- Clasificación narrativa más avanzada
- Sistemas de recomendación
- RAG
- Agentes inteligentes
- Más tipos de obras
- Notificaciones push
- Persistencia avanzada de media
- Aplicación móvil
- Gamificación
- Integraciones con servicios externos

Estas funcionalidades quedan inicialmente fuera del alcance del PFM.

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