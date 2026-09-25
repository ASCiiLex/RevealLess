from django.urls import path
from .views import profile_react_view, edit_profile_react_view
from .api_views import ProfileDetailAPIView, ProfileEditAPIView

urlpatterns = [
    path('editar/', edit_profile_react_view, name='edit_profile'),

    path('api/editar/', ProfileEditAPIView.as_view(), name='profiles_api_edit'),
    path('api/<str:username>/', ProfileDetailAPIView.as_view(), name='profiles_api_detail'),

    path('<str:username>/', profile_react_view, name='profile'),
]