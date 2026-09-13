from rest_framework import serializers
from narrative.models import UnidadNarrativa
from .models import Post


class PostCreateSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=500)
    image = serializers.ImageField(required=False, allow_null=True)
    referencia_narrativa = serializers.PrimaryKeyRelatedField(
        queryset=UnidadNarrativa.objects.all()
    )
    frontera_spoiler = serializers.PrimaryKeyRelatedField(
        queryset=UnidadNarrativa.objects.all(), required=False, allow_null=True
    )
    nivel_spoiler = serializers.ChoiceField(
        choices=['menor', 'importante', 'trama_central'], required=False, default='menor'
    )
    nuevo_progreso = serializers.PrimaryKeyRelatedField(
        queryset=UnidadNarrativa.objects.all(), required=False, allow_null=True
    )
    confirmar_salto_progreso = serializers.BooleanField(required=False, default=False)


class PostUpdateSerializer(serializers.Serializer):
    """Edición de un post ya publicado: todos los campos opcionales
    (partial update), sin la lógica de progreso/IA que sí aplica en la
    creación -- editar no vuelve a consultar el progreso del autor ni
    dispara el asistente de clasificación automática. Si el autor deja
    frontera_spoiler vacío al editar, se interpreta como 'sin cambios'
    (no como 'recalcular con IA'), a diferencia de la creación."""

    text = serializers.CharField(max_length=500, required=False)
    image = serializers.ImageField(required=False, allow_null=True)
    referencia_narrativa = serializers.PrimaryKeyRelatedField(
        queryset=UnidadNarrativa.objects.all(), required=False
    )
    frontera_spoiler = serializers.PrimaryKeyRelatedField(
        queryset=UnidadNarrativa.objects.all(), required=False, allow_null=True
    )
    nivel_spoiler = serializers.ChoiceField(
        choices=['menor', 'importante', 'trama_central'], required=False
    )