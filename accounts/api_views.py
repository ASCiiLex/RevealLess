from django.contrib.auth import authenticate, login
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django_ratelimit.decorators import ratelimit
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import LoginSerializer, RegisterSerializer

# DRF solo comprueba CSRF si ya hay sesión. Login y registro son anónimos: se exige aquí (login CSRF).


@method_decorator(csrf_protect, name='dispatch')
@method_decorator(ratelimit(key='ip', rate='10/m', method='POST', block=True), name='post')
class LoginAPIView(APIView):
    """Límite de 10/m por IP y mensaje genérico ante credenciales inválidas."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            request,
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password'],
        )

        if user is None:
            return Response(
                {'detail': 'Usuario o contraseña incorrectos'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        login(request, user)
        return Response({'username': user.username})


@method_decorator(csrf_protect, name='dispatch')
@method_decorator(ratelimit(key='ip', rate='5/m', method='POST', block=True), name='post')
class RegisterAPIView(APIView):
    """Límite de 5/m por IP. Crea el usuario (el Profile lo crea la señal
    post_save), aplica el avatar si se envió e inicia sesión."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        login(request, user)
        return Response({'username': user.username}, status=status.HTTP_201_CREATED)