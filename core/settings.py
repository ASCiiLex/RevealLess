from pathlib import Path
import os
import sys
from dotenv import load_dotenv
import dj_database_url
from django.templatetags.static import static
from django.urls import reverse_lazy
from django.utils.text import format_lazy

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

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

ALLOWED_HOSTS = [
    'revealless.fly.dev',
    '.fly.dev',
    'localhost',
    '127.0.0.1'
]

CSRF_TRUSTED_ORIGINS = [
    "https://revealless.fly.dev"
]

# Fly.io termina TLS en el edge y reenvía por X-Forwarded-Proto.
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
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600)
    }
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
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ==========================================================
# STATIC / MEDIA
# ==========================================================

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# STATICFILES_STORAGE desapareció en Django 5.1: sin STORAGES se ignoraba en silencio.
# Los tests no ejecutan collectstatic; sin manifiesto, el storage con hash fallaría al renderizar.
_EN_TESTS = 'pytest' in sys.modules
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': (
            'django.contrib.staticfiles.storage.StaticFilesStorage' if _EN_TESTS
            else 'whitenoise.storage.CompressedManifestStaticFilesStorage'
        ),
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

SERVE_MEDIA = os.environ.get('SERVE_MEDIA', 'True' if DEBUG else 'False') == 'True'

# ==========================================================
# LOGIN
# ==========================================================

LOGIN_URL = '/cuentas/login/'
LOGIN_REDIRECT_URL = '/feed/'
LOGOUT_REDIRECT_URL = '/cuentas/login/'

# ==========================================================
# CHANNELS (REDIS EN PRODUCCIÓN / MEMORY EN LOCAL)
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
# DJANGO UNFOLD (tema del admin)
# ==========================================================


def _admin_url(modelo, filtro=''):
    """Listado de un modelo en el admin; perezoso porque las URLs aún no están cargadas."""
    url = reverse_lazy(f'admin:{modelo}_changelist')
    return format_lazy('{}?{}', url, filtro) if filtro else url


def _item(titulo, icono, modelo, filtro='', badge=None):
    item = {'title': titulo, 'icon': icono, 'link': _admin_url(modelo, filtro)}
    if badge:
        item['badge'] = f'core.badges.{badge}'
    return item


PENDIENTE = 'estado__exact=pendiente'

# Menú por tareas, no por app. Un modelo nuevo debe añadirse aquí a mano
# (hasta entonces sigue accesible desde «Todas las aplicaciones»).
NAVEGACION_ADMIN = [
    {
        'title': 'Panel',
        'items': [
            {'title': 'Inicio', 'icon': 'dashboard', 'link': reverse_lazy('admin:index')},
        ],
    },
    {
        'title': 'Pendientes de revisar',
        'separator': True,
        'items': [
            _item('Solicitudes de tema', 'lightbulb', 'narrative_solicitudtema', PENDIENTE,
                  'solicitudes_tema_pendientes'),
            _item('Solicitudes de personaje', 'person_add', 'narrative_solicitudpersonaje', PENDIENTE,
                  'solicitudes_personaje_pendientes'),
            _item('Propuestas de aparición', 'fact_check', 'narrative_propuestaaparicion', PENDIENTE,
                  'propuestas_aparicion_pendientes'),
        ],
    },
    {
        'title': 'Catálogo',
        'separator': True,
        'items': [
            _item('Obras', 'movie', 'narrative_obra'),
            _item('Unidades narrativas', 'account_tree', 'narrative_unidadnarrativa'),
            _item('Categorías', 'sell', 'narrative_categoria'),
            _item('Temas transversales', 'label', 'narrative_tematransversal'),
            _item('IDs externos', 'link', 'narrative_externalid'),
        ],
    },
    {
        'title': 'Personajes',
        'separator': True,
        'items': [
            _item('Personajes', 'groups', 'narrative_personaje'),
            _item('Relevancias', 'military_tech', 'narrative_relevanciapersonaje'),
            _item('Apariciones', 'visibility', 'narrative_propuestaaparicion'),
        ],
    },
    {
        'title': 'Contenido',
        'separator': True,
        'items': [
            _item('Publicaciones', 'article', 'posts_post'),
            _item('Comentarios', 'chat_bubble', 'comments_comment'),
            _item('Hashtags', 'tag', 'posts_hashtag'),
            _item('Reacciones a publicaciones', 'favorite', 'likes_postreaction'),
            _item('Reacciones a comentarios', 'add_reaction', 'comments_commentreaction'),
        ],
    },
    {
        'title': 'Comunidad',
        'separator': True,
        'collapsible': True,
        'items': [
            _item('Suscripciones', 'notifications_active', 'subscriptions_suscripcion'),
            _item('Seguimientos', 'group_add', 'follows_follow'),
            _item('Mensajes', 'mail', 'messages_app_message'),
            _item('Notificaciones', 'notifications', 'notifications_notification'),
            _item('Publicaciones guardadas', 'bookmark', 'saved_posts_savedpost'),
        ],
    },
    {
        'title': 'Usuarios y permisos',
        'separator': True,
        'collapsible': True,
        'items': [
            _item('Usuarios', 'person', 'auth_user'),
            _item('Perfiles', 'badge', 'profiles_profile'),
            _item('Progresos de usuario', 'trending_up', 'narrative_progresousuario'),
            _item('Grupos', 'shield_person', 'auth_group'),
        ],
    },
]

UNFOLD = {
    "SITE_TITLE": "RevealLess admin",
    "SITE_HEADER": "RevealLess",
    "SITE_SYMBOL": "auto_stories",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": NAVEGACION_ADMIN,
    },
    "DASHBOARD_CALLBACK": "core.dashboard.dashboard_callback",
    # Lambda: static() se resuelve por petición, cuando el storage ya está listo.
    "SCRIPTS": [
        lambda request: static("js/admin_busqueda_vivo.js"),
    ],
}

# ==========================================================
# DEFAULTS
# ==========================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'