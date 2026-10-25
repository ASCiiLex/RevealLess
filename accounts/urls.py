from django.urls import path
from .views import logout_view, login_react_view, register_react_view
from .api_views import CambioPasswordAPIView, LoginAPIView, RegisterAPIView

urlpatterns = [
    path('logout/', logout_view, name='logout'),

    path('login/', login_react_view, name='login'),
    path('register/', register_react_view, name='register'),

    path('api/login/', LoginAPIView.as_view(), name='accounts_api_login'),
    path('api/register/', RegisterAPIView.as_view(), name='accounts_api_register'),
    path('api/password/', CambioPasswordAPIView.as_view(), name='accounts_api_password'),
]