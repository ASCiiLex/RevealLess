from rest_framework import serializers
from .models import SavedPost


class SavedPostSerializer(serializers.ModelSerializer):
    post_id = serializers.IntegerField(source='post.id', read_only=True)
    text = serializers.CharField(source='post.text', read_only=True)
    # Composición del post (o portada del vídeo) en miniaturas; sin nada, la tesela muestra el texto.
    imagenes = serializers.SerializerMethodField()
    disposicion = serializers.CharField(source='post.disposicion', read_only=True)

    class Meta:
        model = SavedPost
        fields = ['id', 'post_id', 'text', 'imagenes', 'disposicion', 'created_at']

    def get_imagenes(self, obj):
        return obj.post.imagenes_para_tesela()