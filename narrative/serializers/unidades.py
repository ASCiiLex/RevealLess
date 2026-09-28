from rest_framework import serializers

from ..models import UnidadNarrativa, ProgresoUsuario


class UnidadNarrativaSerializer(serializers.ModelSerializer):
    imagen = serializers.SerializerMethodField()
    padre = serializers.IntegerField(source='padre_id', read_only=True, allow_null=True)
    padre_etiqueta = serializers.SerializerMethodField()

    class Meta:
        model = UnidadNarrativa
        fields = [
            'id',
            'nombre',
            'tipo',
            'etiqueta',
            'orden_inicio',
            'orden_fin',
            'imagen',
            'padre',
            'padre_etiqueta',
        ]

    def get_imagen(self, obj):
        return obj.image_url

    def get_padre_etiqueta(self, obj):
        return obj.padre.etiqueta if obj.padre_id else None


class ProgresoUsuarioSerializer(serializers.ModelSerializer):
    unidad_actual = UnidadNarrativaSerializer(read_only=True)

    class Meta:
        model = ProgresoUsuario
        fields = ['unidad_actual', 'orden_absoluto']