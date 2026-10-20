"""Configuración de Unfold: menú lateral por tareas, contadores y scripts del admin."""

from django.templatetags.static import static
from django.urls import reverse_lazy
from django.utils.text import format_lazy


def _admin_url(modelo, filtro=''):
    """Listado de un modelo en el admin; perezoso porque las URLs aún no están cargadas."""
    url = reverse_lazy(f'admin:{modelo}_changelist')
    return format_lazy('{}?{}', url, filtro) if filtro else url


def _item(titulo, icono, modelo, filtro='', badge=None):
    item = {'title': titulo, 'icon': icono, 'link': _admin_url(modelo, filtro)}
    if badge:
        item['badge'] = f'core.panel.badges.{badge}'
    return item


PENDIENTE = 'estado__exact=pendiente'

# Menú por tareas, no por app. Un modelo nuevo debe añadirse aquí a mano
# (hasta entonces sigue accesible desde «Todas las aplicaciones»).
# Panel y Pendientes siempre abiertos; el resto, plegables.
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
            _item('Solicitudes de obra', 'library_add', 'narrative_solicitudobra', PENDIENTE,
                  'solicitudes_obra_pendientes'),
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
        'collapsible': True,
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
        'collapsible': True,
        'items': [
            _item('Personajes', 'groups', 'narrative_personaje'),
            _item('Relevancias', 'military_tech', 'narrative_relevanciapersonaje'),
            _item('Apariciones', 'visibility', 'narrative_propuestaaparicion'),
        ],
    },
    {
        'title': 'Contenido',
        'separator': True,
        'collapsible': True,
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
        'title': 'IA',
        'separator': True,
        'collapsible': True,
        'items': [
            _item('Usos de IA', 'smart_toy', 'ia_usoia'),
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
    "DASHBOARD_CALLBACK": "core.panel.dashboard.dashboard_callback",
    # Lambda: static() se resuelve por petición, cuando el storage ya está listo.
    "SCRIPTS": [
        lambda request: static("js/admin_busqueda_vivo.js"),
    ],
}