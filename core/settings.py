from pathlib import Path
import os
import sys
from dotenv import load_dotenv
import dj_database_url

from .configuracion_admin import UNFOLD  # noqa: F401 (Unfold lo lee de settings)

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

_EN_TESTS = 'pytest' in sys.modules

# ==========================================================
# SEGURIDAD
# ==========================================================

DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'

SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'clave-solo-para-desarrollo-local'
    else:
        sys.exit("SECRET_KEY no definida en el entorno de producción.")

_HOSTS_LOCALES = ['localhost', '127.0.0.1']
# Dominios propios separados por comas. Render inyecta RENDER_EXTERNAL_HOSTNAME en cada servicio web.
_HOSTS_EXTRA = [h.strip() for h in os.environ.get('DJANGO_ALLOWED_HOSTS', '').split(',') if h.strip()]
_HOST_RENDER = os.environ.get('RENDER_EXTERNAL_HOSTNAME')

ALLOWED_HOSTS = _HOSTS_LOCALES + _HOSTS_EXTRA + ([_HOST_RENDER] if _HOST_RENDER else [])
CSRF_TRUSTED_ORIGINS = [
    f'https://{h}' for h in ALLOWED_HOSTS if h not in _HOSTS_LOCALES and not h.startswith('.')
]

# Render termina TLS en su proxy y reenvía el esquema original en X-Forwarded-Proto.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
# CSRF_COOKIE_HTTPONLY debe ser False: el patrón double-submit-cookie de
# Django exige que JS pueda leer csrftoken para reenviarlo en la cabecera
# X-CSRFToken. No es un secreto de sesión -- su protección viene de la
# Same-Origin Policy, no de ocultarlo a JS. Con HTTPONLY=True, todo POST
# desde React llega sin token válido -> 403.
CSRF_COOKIE_HTTPONLY = False
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14  # 14 días
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG

# ==========================================================
# APLICACIONES
# ==========================================================

INSTALLED_APPS = [
    'unfold',  # antes de django.contrib.admin

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    "django_extensions",
    "rest_framework",

    'core',

    'profiles',
    'posts',
    'comments',
    'likes',
    'follows',
    'feed',
    'accounts',
    'notifications',
    'messages_app',
    'saved_posts',
    'narrative',
    'subscriptions',

    'channels',
]

# ==========================================================
# MIDDLEWARE
# ==========================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Peticiones más lentas que el umbral quedan en los logs con sus consultas y su tiempo en BD.
RENDIMIENTO_UMBRAL_MS = int(os.environ.get('RENDIMIENTO_UMBRAL_MS', '500'))
if not _EN_TESTS:
    MIDDLEWARE.insert(0, 'core.rendimiento.RegistroLentitudMiddleware')

# ==========================================================
# URLS / TEMPLATES
# ==========================================================

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'core' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# ==========================================================
# ASGI / WSGI
# ==========================================================

ASGI_APPLICATION = 'core.asgi.application'
WSGI_APPLICATION = 'core.wsgi.application'

# ==========================================================
# BASE DE DATOS
# ==========================================================

DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    DATABASES = {'default': dj_database_url.parse(DATABASE_URL)}
    # Pool de psycopg 3: reutiliza conexiones entre peticiones. Bajo ASGI Django desaconseja CONN_MAX_AGE,
    # y abrir una conexión por petición (proceso nuevo + autenticación SCRAM) satura un Postgres de 0,1 CPU.
    DATABASES['default']['OPTIONS'] = {'pool': {'min_size': 2, 'max_size': 10, 'timeout': 10}}
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DATABASE_NAME', 'revealless'),
            'USER': os.environ.get('DATABASE_USER', 'revealless'),
            'PASSWORD': os.environ.get('DATABASE_PASSWORD', ''),
            'HOST': os.environ.get('DATABASE_HOST', 'localhost'),
            'PORT': os.environ.get('DATABASE_PORT', '5433'),
        }
    }

# ==========================================================
# PASSWORDS
# ==========================================================

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ==========================================================
# INTERNACIONALIZACIÓN
# ==========================================================

# Traduce también los textos de Django, DRF y Unfold (admin, validaciones de la API).
LANGUAGE_CODE = 'es'
# La BD sigue guardando UTC; esto solo afecta a la presentación y a los cortes por día.
TIME_ZONE = 'Europe/Madrid'
USE_I18N = True
USE_TZ = True

# ==========================================================
# STATIC / MEDIA
# ==========================================================

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Imágenes subidas en Tigris (S3) si hay bucket configurado; nunca en tests.
_USAR_TIGRIS = bool(os.environ.get('AWS_STORAGE_BUCKET_NAME')) and not _EN_TESTS

if _USAR_TIGRIS:
    _MEDIA_STORAGE = {
        'BACKEND': 'storages.backends.s3.S3Storage',
        'OPTIONS': {
            'bucket_name': os.environ['AWS_STORAGE_BUCKET_NAME'],
            'access_key': os.environ.get('AWS_ACCESS_KEY_ID'),
            'secret_key': os.environ.get('AWS_SECRET_ACCESS_KEY'),
            'endpoint_url': os.environ.get('AWS_S3_ENDPOINT_URL', 'https://t3.storage.dev'),
            'region_name': 'auto',
            'addressing_style': 'virtual',
            'signature_version': 's3v4',
            # Bucket privado y URLs firmadas: solo recibe la URL quien puede ver el contenido.
            'querystring_auth': True,
            'querystring_expire': 60 * 60 * 6,
            'file_overwrite': False,
        },
    }
else:
    _MEDIA_STORAGE = {'BACKEND': 'django.core.files.storage.FileSystemStorage'}

# STATICFILES_STORAGE desapareció en Django 5.1: sin STORAGES se ignoraba en silencio.
# Los tests no ejecutan collectstatic; sin manifiesto, el storage con hash fallaría al renderizar.
STORAGES = {
    'default': _MEDIA_STORAGE,
    'staticfiles': {
        'BACKEND': (
            'django.contrib.staticfiles.storage.StaticFilesStorage' if _EN_TESTS
            else 'whitenoise.storage.CompressedManifestStaticFilesStorage'
        ),
    },
}

SERVE_MEDIA = not _USAR_TIGRIS and os.environ.get('SERVE_MEDIA', 'True' if DEBUG else 'False') == 'True'

# ==========================================================
# LOGIN
# ==========================================================

LOGIN_URL = '/cuentas/login/'
LOGIN_REDIRECT_URL = '/feed/'
LOGOUT_REDIRECT_URL = '/cuentas/login/'

# ==========================================================
# CHANNELS (REDIS SI HAY VARIAS INSTANCIAS / MEMORIA CON UNA)
# ==========================================================

REDIS_URL = os.environ.get("REDIS_URL")

if REDIS_URL:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [REDIS_URL],
            },
        },
    }
else:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        },
    }

# ==========================================================
# RATE LIMIT E IA
# ==========================================================

# IP real del cliente tras el proxy de Render (X-Forwarded-For es falsificable).
RATELIMIT_IP_META_KEY = 'core.red.ip_cliente'

# Llamadas a la IA por usuario al publicar sin frontera; superado, se usa el progreso del autor.
IA_LIMITE_PUBLICAR = os.environ.get('IA_LIMITE_PUBLICAR', '20/h')

# ==========================================================
# DJANGO REST FRAMEWORK
# ==========================================================

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 12,
}

# ==========================================================
# LOGGING
# ==========================================================

# A consola: Render recoge stdout/stderr en sus logs.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {'format': '{levelname} {name}: {message}', 'style': '{'},
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'simple'},
    },
    'root': {'handlers': ['console'], 'level': 'WARNING'},
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.environ.get('DJANGO_LOG_LEVEL', 'WARNING'),
            'propagate': False,
        },
    },
}

# ==========================================================
# DEFAULTS
# ==========================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configuración del admin (Unfold): core/configuracion_admin.py