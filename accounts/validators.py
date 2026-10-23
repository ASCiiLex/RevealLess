from django.core.validators import RegexValidator

# La sala del chat es chat_<a>_<b>, y Channels exige nombres de grupo de menos de 100 caracteres.
USERNAME_MAX = 30

# Lo que ya dan por hecho las rutas (perfil, chat), las menciones (@\w+) y los grupos de Channels (ASCII).
validar_username = RegexValidator(
    r'^[A-Za-z0-9_]+\Z',
    'Usa solo letras sin acentos, números y guion bajo.',
)