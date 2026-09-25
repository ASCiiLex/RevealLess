from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User


def profile_view(request, username):
    return redirect('profile_react', username=username)


def followers_view(request, username):
    return redirect('followers_react', username=username)


def following_view(request, username):
    return redirect('following_react', username=username)


def profile_react_view(request, username):
    """Monta React para el perfil. Sin login: los perfiles son públicos."""
    get_object_or_404(User, username=username)
    return render(request, 'profiles/profile_react.html', {'username': username})


@login_required
def edit_profile_react_view(request):
    return render(request, 'profiles/edit_profile_react.html')