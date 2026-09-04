from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Follow

@login_required
def follow_user(request, username):
    target = get_object_or_404(User, username=username)

    if target != request.user:
        Follow.objects.get_or_create(
            follower=request.user,
            followed=target
        )

    return redirect('profile', username=username)


@login_required
def unfollow_user(request, username):
    target = get_object_or_404(User, username=username)

    Follow.objects.filter(
        follower=request.user,
        followed=target
    ).delete()

    return redirect('profile', username=username)


def followers_list(request, username):
    user_obj = get_object_or_404(User, username=username)
    followers = Follow.objects.filter(followed=user_obj).select_related('follower')

    return render(request, 'follows/followers_list.html', {
        'profile_user': user_obj,
        'followers': followers,
    })


def following_list(request, username):
    user_obj = get_object_or_404(User, username=username)
    following = Follow.objects.filter(follower=user_obj).select_related('followed')

    return render(request, 'follows/following_list.html', {
        'profile_user': user_obj,
        'following': following,
    })