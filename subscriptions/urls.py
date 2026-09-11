from django.urls import path
from .views import suscripciones_react_view
from .api_views import SuscripcionListCreateAPIView, SuscripcionDeleteAPIView, SuscripcionToggleActivaAPIView

urlpatterns = [
    path('suscripciones/', suscripciones_react_view, name='subscriptions_react'),

    path('api/suscripciones/', SuscripcionListCreateAPIView.as_view(), name='subscriptions_api_list'),
    path('api/suscripciones/<int:pk>/', SuscripcionDeleteAPIView.as_view(), name='subscriptions_api_delete'),
    path('api/suscripciones/<int:pk>/activa/', SuscripcionToggleActivaAPIView.as_view(), name='subscriptions_api_toggle'),
]