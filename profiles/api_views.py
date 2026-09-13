from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from follows.models import Follow
from .models import Profile
from .serializers import ProfileDetailSerializer, ProfileEditSerializer


class ProfileDetailAPIView(APIView):
    """Réplica de profile_view: mismos datos (posts visibles vía
    visible_for(), contadores de followers/following, is_following).
    AllowAny porque los perfiles son públicos -- visible_for() ya
    contempla usuarios anónimos (devuelve queryset vacío), igual que en
    Django clásico."""

    permission_classes = [AllowAny]

    def get(self, request, username):
        profile_user = get_object_or_404(User, username=username)
        profile = get_object_or_404(Profile.objects.select_related('user'), user=profile_user)

        posts = (
            profile_user.posts.all()
            .select_related('author', 'obra')
            .visible_for(request.user)
            .order_by('-created_at')
        )

        is_following = False
        if request.user.is_authenticated and request.user != profile_user:
            is_following = Follow.objects.filter(
                follower=request.user, followed=profile_user
            ).exists()

        data = {
            'profile_user': profile_user,
            'profile': profile,
            'posts': posts,
            'is_following': is_following,
            'followers_count': Follow.objects.filter(followed=profile_user).count(),
            'following_count': Follow.objects.filter(follower=profile_user).count(),
        }

        serializer = ProfileDetailSerializer(data, context={'request': request})
        return Response(serializer.data)


class ProfileEditAPIView(APIView):
    """Réplica de edit_profile. PATCH en vez de PUT: permite enviar solo
    los campos que cambian (típico en un formulario de edición desde
    React que no siempre reenvía la imagen si no se tocó)."""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        profile = request.user.profile
        return Response({
            'username': request.user.username,
            'email': request.user.email,
            'bio': profile.bio,
            'interests': profile.interests,
            'avatar_url': profile.image_url,
        })

    def patch(self, request):
        profile = request.user.profile
        serializer = ProfileEditSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'username': request.user.username,
            'email': request.user.email,
            'bio': profile.bio,
            'interests': profile.interests,
            'avatar_url': profile.image_url,
        })