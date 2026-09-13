from rest_framework import serializers
from narrative.models import UnidadNarrativa
from .models import Post


class PostCreateSerializer(serializers.Serializer):
    """Entrada del formulario unificado de creación de post. No es un
    ModelSerializer porque la asignación de frontera_spoiler/
    frontera_origen depende de lógica condicional (IA, fallback,
    actualización de progreso) que vive en create_post_view, replicando
    exactamente create_post -- este serializer solo valida la forma de
    los datos de entrada."""

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