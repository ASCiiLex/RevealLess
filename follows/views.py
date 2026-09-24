from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User


def followers_react_view(request, username):
    """Monta React para la lista de seguidores."""
    get_object_or_404(User, username=username)
    return render(request, 'follows/followers_react.html', {'username': username})


def following_react_view(request, username):
    get_object_or_404(User, username=username)
    return render(request, 'follows/following_react.html', {'username': username})