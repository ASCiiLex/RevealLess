from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils.http import url_has_allowed_host_and_scheme

from posts.models import Post
from .models import SavedPost


def _safe_redirect(request, post_id):
    referer = request.META.get("HTTP_REFERER")
    if referer and url_has_allowed_host_and_scheme(
        referer, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return redirect(referer)
    return redirect("post_detail", post_id=post_id)


@login_required
@require_POST
def save_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    SavedPost.objects.get_or_create(user=request.user, post=post)
    return _safe_redirect(request, post_id)


@login_required
@require_POST
def unsave_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    SavedPost.objects.filter(user=request.user, post=post).delete()
    return _safe_redirect(request, post_id)


@login_required
def saved_posts_view(request):
    saved = SavedPost.objects.filter(user=request.user).select_related(
        "post", "post__author"
    )
    return render(request, "saved_posts/saved_posts.html", {"saved": saved})
