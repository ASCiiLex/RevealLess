from rest_framework import serializers

from ..models import SolicitudObra


class SolicitudObraSerializer(serializers.ModelSerializer):
    obra_slug = serializers.CharField(source='obra.slug', read_only=True, default=None)

    class Meta:
        model = SolicitudObra
        fields = ['id', 'titulo', 'tipo', 'enlace', 'comentario', 'estado', 'obra_slug', 'creado_en', 'resuelto_en']
        read_only_fields = ['estado', 'creado_en', 'resuelto_en']