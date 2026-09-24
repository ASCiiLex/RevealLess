from django.urls import path
from .views import logout_view, login_react_view, register_react_view
from .api_views import LoginAPIView, RegisterAPIView

urlpatterns = [
    path('logout/', logout_view, name='logout'),

    path('login-react/', login_react_view, name='login_react'),
    path('register-react/', register_react_view, name='register_react'),

    path('api/login/', LoginAPIView.as_view(), name='accounts_api_login'),
    path('api/register/', RegisterAPIView.as_view(), name='accounts_api_register'),
]