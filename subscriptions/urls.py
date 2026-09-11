from django.urls import path
from .api_views import SuscripcionListCreateAPIView, SuscripcionDeleteAPIView

urlpatterns = [
    path('api/suscripciones/', SuscripcionListCreateAPIView.as_view(), name='subscriptions_api_list'),
    path('api/suscripciones/<int:pk>/', SuscripcionDeleteAPIView.as_view(), name='subscriptions_api_delete'),
]