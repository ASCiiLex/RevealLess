from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
from .models import Follow


@login_required
@require_POST
def follow_user(request, username):
    target = get_object_or_404(User, username=username)
    if target != request.user:
        Follow.objects.get_or_create(follower=request.user, followed=target)
    return redirect("profile", username=username)


@login_required
@require_POST
def unfollow_user(request, username):
    target = get_object_or_404(User, username=username)
    Follow.objects.filter(follower=request.user, followed=target).delete()
    return redirect("profile", username=username)


def followers_list(request, username):
    user_obj = get_object_or_404(User, username=username)
    followers = Follow.objects.filter(followed=user_obj).select_related("follower")
    return render(
        request,
        "follows/followers_list.html",
        {
            "profile_user": user_obj,
            "followers": followers,
        },
    )


def following_list(request, username):
    user_obj = get_object_or_404(User, username=username)
    following = Follow.objects.filter(follower=user_obj).select_related("followed")
    return render(
        request,
        "follows/following_list.html",
        {
            "profile_user": user_obj,
            "following": following,
        },
    )


def followers_react_view(request, username):
    """Vista mínima que monta el punto de entrada de React para la
    lista de seguidores (Fase 4). No reemplaza followers_list."""
    get_object_or_404(User, username=username)
    return render(request, 'follows/followers_react.html', {'username': username})


def following_react_view(request, username):
    get_object_or_404(User, username=username)
    return render(request, 'follows/following_react.html', {'username': username})