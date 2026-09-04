from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from posts.models import Post
from .models import SavedPost


@login_required
def save_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    SavedPost.objects.get_or_create(user=request.user, post=post)
    return redirect(request.META.get('HTTP_REFERER', '/'))


@login_required
def unsave_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    SavedPost.objects.filter(user=request.user, post=post).delete()
    return redirect(request.META.get('HTTP_REFERER', '/'))


@login_required
def saved_posts_view(request):
    # Cargar posts guardados con select_related correcto
    saved = (
        SavedPost.objects
        .filter(user=request.user)
        .select_related('post', 'post__author')
    )

    return render(request, 'saved_posts/saved_posts.html', {
        'saved': saved
    })