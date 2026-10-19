# RevealLess — red social sin spoilers

**Demo:** https://www.revealless.es

Red social para conversar sobre series, películas, libros y manga en la que **cada usuario solo ve lo que su progreso le permite ver**. En lugar de pedir al lector que esquive los spoilers, el sistema compara su progreso declarado en cada obra con la frontera de cada publicación y decide por él.

```text
progreso_usuario >= frontera_contenido  →  visible
```

Proyecto Final del Máster en Desarrollo Full Stack (Conquer Blocks). Parte de un proyecto previo de red social en Django (`RedSocial_Django`), auditado, saneado y ampliado con un dominio propio.

---

## Funcionalidades

**Motor antispoiler**
- Visibilidad por progreso aplicada en feed, perfil, detalle de publicación, comentarios, contadores y personajes.
- Cada obra se modela como un árbol de profundidad variable (parte, saga, arco, episodio o capítulo); la comparación es siempre entre enteros.
- Progreso por obra: avance y retroceso, con confirmación explícita en los saltos grandes.
- Continuidades: adaptaciones (anime/manga, libro/película) y universos compartidos, con referencias cruzadas detectadas al publicar y publicaciones comparativas («misma escena en otro formato» o «comparativa»).
- Personajes cuyo nombre, imagen y relevancia cambian según el progreso del lector.

**IA como asistente, no como oráculo**
- Claude (Anthropic) propone la frontera de una publicación —la revelación más tardía que da por sabida el texto— con su nivel de certeza, y el autor decide.
- Si la IA falla, tarda o no está segura, la frontera cae al progreso del autor: nunca se publica nada sin proteger. Una propuesta en una unidad sin título («Episodio N») nunca se aplica sola.
- Los hechos que identifica la IA no salen nunca del servidor; la sugerencia y la clasificación al publicar tienen límite de uso por usuario.

**Red social**
- Publicaciones con parte, tema o frontera; galería de hasta cuatro imágenes con encuadre; personajes enfrentados; emoción del autor.
- Comentarios anidados (tres niveles) que heredan la frontera de su publicación o declaran la suya.
- Seguir usuarios, obras, partes, temas y personajes; silenciar suscripciones.
- Reacciones con once emociones, publicaciones guardadas, chat y notificaciones en tiempo real.
- Panel de administración (Unfold) con métricas y colas de revisión (temas, personajes y apariciones propuestos).

---

## Stack

| Capa | Tecnología |
|---|---|
| Backend | Django 5.2, Django REST Framework, Django Channels + Daphne (ASGI) |
| Base de datos | PostgreSQL (psycopg 3 con pool de conexiones en producción) |
| Frontend | React 18 + TypeScript + Vite 5, CSS Modules. React embebido por vista: cada página Django carga solo su *bundle* |
| IA | Anthropic Claude Haiku 4.5 mediante `tool_use` (salida JSON estructurada) |
| Estáticos e imágenes | WhiteNoise; imágenes subidas en Tigris (S3) con URLs firmadas |
| Seguridad | Cabeceras `SECURE_*`, CSRF, validación de entradas, `django-ratelimit`, validación de origen en WebSockets |
| Tests | pytest + pytest-django |
| Despliegue | Render (Docker) + Postgres gestionado + Tigris, con dominio propio |

---

## Estructura

```text
RevealLess/
├── core/            # settings, URLs, ASGI, almacenamiento, rendimiento y utilidades comunes
├── narrative/       # dominio propio: obras, unidades, progreso, motor de visibilidad, IA, catálogo
├── posts/           # publicaciones, galerías, comparativas
├── comments/        # comentarios anidados
├── subscriptions/   # suscripciones y silenciado
├── accounts/ profiles/ follows/ likes/ saved_posts/
├── messages_app/ notifications/   # tiempo real (Channels)
├── feed/            # feed y landing pública
├── frontend/        # React + Vite
├── static/          # estáticos propios (el build de Vite va a static/frontend/dist)
├── Dockerfile
└── render.yaml
```

---

## Instalación local

Requisitos: Python 3.12, Node.js 20 o superior y PostgreSQL.

```bash
git clone git@github.com:ASCiiLex/RevealLess.git
cd RevealLess

python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env              # y rellena los valores
python manage.py migrate
python manage.py createsuperuser

cd frontend && npm install && cd ..
```

### Variables de entorno

| Variable | Uso |
|---|---|
| `DJANGO_DEBUG` | `True` en local (activa el servidor de Vite y los avisos de depuración) |
| `SECRET_KEY` | Obligatoria en producción; sin ella la app no arranca |
| `DATABASE_*` o `DATABASE_URL` | Conexión a PostgreSQL |
| `ANTHROPIC_API_KEY` | Clave de la IA; sin ella, la frontera cae al progreso del autor |
| `ANTHROPIC_MODEL` | Opcional: cambia el modelo de la clasificación |
| `IA_LIMITE_PUBLICAR` | Opcional: llamadas a la IA por usuario al publicar (por defecto `20/h`) |
| `RENDIMIENTO_UMBRAL_MS` | Opcional: peticiones más lentas que el umbral quedan en los logs (por defecto `500`) |
| `AWS_*` | Solo producción: bucket y credenciales de Tigris |
| `DJANGO_ALLOWED_HOSTS` | Solo producción: dominios propios, separados por comas |

### Ejecutar

Dos terminales:

```bash
# Terminal 1: frontend con recarga en caliente
cd frontend && npm run dev

# Terminal 2: Django en modo ASGI (necesario para chat y notificaciones)
daphne -b 127.0.0.1 -p 8000 core.asgi:application
```

La app queda en `http://localhost:8000`. Daphne no recarga solo: reinícialo tras cambiar código del backend.

### Tests

```bash
pytest
```

Ningún test llama a la API real de la IA ni a servicios externos.

### Catálogo

Las obras se cargan con comandos de gestión; las estructuras curadas a mano están en `narrative/data/*.yaml`.

| Comando | Para qué |
|---|---|
| `importar_catalogo` | Metadatos y episodios desde Jikan (MyAnimeList) |
| `crear_obra_manual` | Alta de una obra sin fuente externa |
| `importar_estructura` | Aplica un YAML con el árbol de partes, sagas y arcos |
| `importar_personajes` / `cargar_personajes` / `copiar_personajes` | Personajes desde Wikidata, YAML o entre adaptaciones |
| `recalcular_orden` | Recalcula el orden narrativo de una obra |

Opciones de cada comando: `python manage.py help <comando>`.

---

## Uso

1. Regístrate y elige las obras que sigues.
2. Declara por dónde vas en cada una (árbol de progreso o ajuste fino).
3. Publica: elige obra y parte o tema, escribe y, si quieres, pide a la IA que sugiera la frontera. Revísala siempre antes de publicar.
4. El feed muestra solo lo que tu progreso permite; al avanzar, aparece el contenido que ya puedes ver.

---

## Despliegue (Render + Tigris)

`render.yaml` define el servicio web (Docker, Frankfurt) y la base de datos Postgres gestionada. El `Dockerfile` compila el frontend, ejecuta `collectstatic` y sirve la app con Daphne; las migraciones se aplican antes de cada despliegue y, si fallan, se mantiene la versión anterior.

1. **Tigris:** bucket privado y una clave con permiso de lectura y escritura solo sobre él.
2. **Render:** *New → Blueprint*, conecta el repositorio y rellena `ANTHROPIC_API_KEY`, `AWS_STORAGE_BUCKET_NAME`, `AWS_ACCESS_KEY_ID` y `AWS_SECRET_ACCESS_KEY`. `SECRET_KEY` y `DATABASE_URL` se generan solas.
3. **Datos:** restaura la base de datos con `pg_restore` y sube las imágenes al bucket:

```bash
   aws s3 sync media/ s3://<bucket>/ --endpoint-url https://t3.storage.dev
```

4. **Dominio propio:** añádelo en *Settings → Custom Domains*, crea en el DNS los registros que indica Render y pon el dominio en `DJANGO_ALLOWED_HOSTS`.

Cada *push* a la rama principal despliega automáticamente.

---

## Copias de seguridad

- **Automática:** Render permite recuperar la base de datos a cualquier momento de los últimos 3 días (plan Hobby), desde la pestaña *Recovery* de la base de datos.
- **Manual:** un volcado antes de cada cambio importante (migraciones, cargas de datos) y semanalmente mientras la app esté en revisión.

Producción usa Postgres 18; el volcado se hace con la imagen oficial para no depender de la versión de `pg_dump` instalada:

```bash
read -rs RENDER_DB_URL            # pega la External Database URL (no se muestra ni queda en el historial)
docker run --rm postgres:18 pg_dump -Fc --no-owner --no-privileges \
  --exclude-table-data=django_session -d "$RENDER_DB_URL" \
  > ~/backups/revealless/prod_$(date +%Y%m%d_%H%M).dump
chmod 600 ~/backups/revealless/prod_*.dump
unset RENDER_DB_URL
```

Para restaurar un volcado (sustituye por completo la base de datos de producción; solo ante una emergencia):

```bash
read -rs RENDER_DB_URL
docker run --rm -v ~/backups/revealless:/copias postgres:18 pg_restore \
  --clean --if-exists --no-owner --no-privileges --single-transaction --exit-on-error \
  -d "$RENDER_DB_URL" /copias/<archivo>.dump
unset RENDER_DB_URL
```

Los volcados contienen los hashes de las contraseñas de los usuarios: se guardan fuera del repositorio y con permisos `600`.

---

## Documentación

La memoria técnica del proyecto (decisiones de diseño, seguridad, casos de uso y evolución) se entrega aparte del repositorio.

## Autor

Desarrollado por **Álex** como Proyecto Final del Máster en Desarrollo Full Stack. Proyecto personal con fines educativos y de portfolio.