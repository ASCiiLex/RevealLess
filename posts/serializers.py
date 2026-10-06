from rest_framework import serializers
from narrative.models import ClasificacionNarrativa, Obra, Personaje, TemaTransversal, UnidadNarrativa
from .models import Post


EMOCION_CHOICES = [c[0] for c in ClasificacionNarrativa.EMOCION_CHOICES]
DISPOSICIONES = [c[0] for c in Post.DISPOSICION_CHOICES]
MODOS_CRUCE = [c[0] for c in Post.MODO_CRUCE_CHOICES]


class PostCreateSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=500)
    image = serializers.ImageField(required=False, allow_null=True)
    # Galería (2 a 4). Con una sola se guarda como `image`.
    imagenes = serializers.ListField(
        child=serializers.ImageField(), required=False, max_length=Post.MAX_IMAGENES,
    )
    etiquetas = serializers.ListField(
        child=serializers.CharField(max_length=40, allow_blank=True), required=False,
    )
    disposicion = serializers.ChoiceField(choices=DISPOSICIONES, required=False, allow_blank=True)
    personajes_comparados = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(queryset=Personaje.objects.all()),
        required=False,
        max_length=Post.MAX_COMPARADOS,
    )
    # Nombres que aún no existen (o el autor no encuentra): quedan como solicitud.
    personajes_propuestos = serializers.ListField(
        child=serializers.CharField(max_length=150), required=False, max_length=Post.MAX_COMPARADOS,
    )
    # Opcional si el post habla de un tema.
    referencia_narrativa = serializers.PrimaryKeyRelatedField(
        queryset=UnidadNarrativa.objects.all(), required=False, allow_null=True,
    )
    frontera_spoiler = serializers.PrimaryKeyRelatedField(
        queryset=UnidadNarrativa.objects.all(), required=False, allow_null=True
    )
    nivel_spoiler = serializers.ChoiceField(
        choices=['menor', 'importante', 'trama_central'], required=False, default='menor'
    )
    emocion_autor = serializers.ChoiceField(
        choices=EMOCION_CHOICES, required=False, allow_null=True
    )
    tema = serializers.PrimaryKeyRelatedField(
        queryset=TemaTransversal.objects.all(), required=False, allow_null=True
    )
    # Tema escrito a mano: se usa si ya existe en la obra; si no, queda como solicitud pendiente.
    tema_propuesto = serializers.CharField(max_length=150, required=False, allow_blank=True)
    nuevo_progreso = serializers.PrimaryKeyRelatedField(
        queryset=UnidadNarrativa.objects.all(), required=False, allow_null=True
    )
    confirmar_salto_progreso = serializers.BooleanField(required=False, default=False)
    obra_cruzada = serializers.PrimaryKeyRelatedField(
        queryset=Obra.objects.all(), required=False, allow_null=True
    )
    frontera_cruzada = serializers.PrimaryKeyRelatedField(
        queryset=UnidadNarrativa.objects.all(), required=False, allow_null=True
    )
    modo_cruce = serializers.ChoiceField(choices=MODOS_CRUCE, required=False)
    descartar_referencia_cruzada = serializers.BooleanField(required=False, default=False)


class PostUpdateSerializer(serializers.Serializer):
    """Edición de un post ya publicado: todos los campos opcionales
    (partial update), sin la lógica de progreso/IA que sí aplica en la
    creación -- editar no vuelve a consultar el progreso del autor ni
    dispara el asistente de clasificación automática, ni la detección
    de referencia cruzada. Si el autor deja frontera_spoiler vacío al
    editar, se interpreta como 'sin cambios' (no como 'recalcular con
    IA'), a diferencia de la creación."""

    text = serializers.CharField(max_length=500, required=False)
    image = serializers.ImageField(required=False, allow_null=True)
    # La imagen es opcional: el autor puede retirarla. Una imagen nueva tiene prioridad.
    quitar_imagen = serializers.BooleanField(required=False, default=False)
    referencia_narrativa = serializers.PrimaryKeyRelatedField(
        queryset=UnidadNarrativa.objects.all(), required=False
    )
    frontera_spoiler = serializers.PrimaryKeyRelatedField(
        queryset=UnidadNarrativa.objects.all(), required=False, allow_null=True
    )
    nivel_spoiler = serializers.ChoiceField(
        choices=['menor', 'importante', 'trama_central'], required=False
    )
    emocion_autor = serializers.ChoiceField(
        choices=EMOCION_CHOICES, required=False, allow_null=True
    )
    tema = serializers.PrimaryKeyRelatedField(
        queryset=TemaTransversal.objects.all(), required=False, allow_null=True
    )
    obra_cruzada = serializers.PrimaryKeyRelatedField(
        queryset=Obra.objects.all(), required=False, allow_null=True
    )
    frontera_cruzada = serializers.PrimaryKeyRelatedField(
        queryset=UnidadNarrativa.objects.all(), required=False, allow_null=True
    )