from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Profile


class ProfilePostSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    text = serializers.CharField()
    imagenes = serializers.ListField(child=serializers.DictField())
    disposicion = serializers.CharField(allow_blank=True)


class ProfileDetailSerializer(serializers.Serializer):
    username = serializers.CharField(source='profile_user.username')
    bio = serializers.CharField(source='profile.bio')
    interests = serializers.CharField(source='profile.interests')
    avatar_url = serializers.CharField(source='profile.image_url')
    is_own_profile = serializers.SerializerMethodField()
    is_following = serializers.BooleanField()
    followers_count = serializers.IntegerField()
    following_count = serializers.IntegerField()
    posts = serializers.SerializerMethodField()
    has_hidden_posts = serializers.SerializerMethodField()

    def get_is_own_profile(self, obj):
        request = self.context['request']
        return request.user.is_authenticated and request.user == obj['profile_user']

    def get_posts(self, obj):
        # Composición del post (o portada del vídeo) en miniaturas; sin nada, la tesela muestra el texto.
        return [
            {
                'id': p.id, 'text': p.text,
                'imagenes': p.imagenes_para_tesela(), 'disposicion': p.disposicion,
            }
            for p in obj['posts']
        ]

    def get_has_hidden_posts(self, obj):
        """True si el usuario tiene posts publicados que no aparecen en
        'posts' porque visible_for() los oculta (progreso insuficiente
        del visitante) -- distinto de 'no tiene publicaciones en
        absoluto'. Usado por el frontend para elegir el mensaje
        correcto en el estado vacio."""
        return obj['total_posts_publicados'] > len(obj['posts'])


class ProfileEditSerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()

    class Meta:
        model = Profile
        fields = ['username', 'email', 'bio', 'interests', 'image']
        extra_kwargs = {'image': {'required': False}}

    def validate_username(self, value):
        user = self.instance.user
        if User.objects.filter(username=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError('Este nombre de usuario ya está en uso.')
        return value

    def validate_email(self, value):
        user = self.instance.user
        if User.objects.filter(email=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError('Este email ya está en uso.')
        return value

    def update(self, instance, validated_data):
        user = instance.user
        user.username = validated_data.pop('username')
        user.email = validated_data.pop('email')
        user.save()

        return super().update(instance, validated_data)