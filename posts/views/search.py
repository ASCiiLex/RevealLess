from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.db.models import Count

from ..models import Hashtag, Post


@login_required
def mentions_search(request):
    q = request.GET.get('q', '').strip()
    results = []

    if q:
        users = User.objects.filter(username__istartswith=q).order_by('username')[:10]
        results = [{'username': u.username} for u in users]

    return JsonResponse({'results': results})


@login_required
def hashtags_search(request):
    q = request.GET.get('q', '').strip()
    results = []

    if q:
        tags = Hashtag.objects.filter(name__istartswith=q).order_by('name')[:10]
        results = [{'name': t.name} for t in tags]

    return JsonResponse({'results': results})


@login_required
def suggested_hashtags(request):
    tags = Hashtag.objects.annotate(
        num_posts=Count('posts__post')
    ).order_by('-num_posts')[:10]

    return JsonResponse({
        'results': [t.name for t in tags]
    })


def global_search(request):
    q = request.GET.get('q', '').strip()

    users_data = []
    hashtags_data = []
    posts_data = []

    if q:
        users_qs = (
            User.objects.filter(username__icontains=q)
            .select_related('profile')
            .order_by('username')[:5]
        )
        for u in users_qs:
            img = u.profile.image.url if hasattr(u, "profile") and getattr(u.profile, "image", None) else "/static/img/default_profile.jpg"
            users_data.append({
                "username": u.username,
                "image": img,
            })

        hashtags_qs = (
            Hashtag.objects.filter(name__icontains=q)
            .order_by('name')[:5]
        )
        hashtags_data = [{"name": h.name} for h in hashtags_qs]

        posts_qs = (
            Post.objects.visible_for(request.user)
            .filter(text__icontains=q)
            .order_by('-created_at')[:5]
        )
        for p in posts_qs:
            p_img = p.image.url if getattr(p, "image", None) else "/static/img/default_post.jpg"
            posts_data.append({
                "id": p.id,
                "text": p.text,
                "image": p_img,
            })

    return JsonResponse({
        'users': users_data,
        'hashtags': hashtags_data,
        'posts': posts_data,
    })