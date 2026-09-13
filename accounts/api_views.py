from django.contrib.auth import authenticate, login
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import LoginSerializer, RegisterSerializer


@method_decorator(ratelimit(key='ip', rate='10/m', method='POST', block=True), name='post')
class LoginAPIView(APIView):
    """Mismo límite de tasa que login_view (10/m por IP), mismo mensaje
    de error genérico ante credenciales inválidas."""

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


@method_decorator(ratelimit(key='ip', rate='5/m', method='POST', block=True), name='post')
class RegisterAPIView(APIView):
    """Mismo límite de tasa que register_view (5/m por IP). Crea el
    usuario (Profile se crea solo vía la señal post_save ya existente),
    aplica el avatar si se envió, e inicia sesión automáticamente,
    igual que el flujo Django clásico."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        login(request, user)
        return Response({'username': user.username}, status=status.HTTP_201_CREATED)