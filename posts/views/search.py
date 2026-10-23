from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.db.models import Q

from follows.models import Follow
from ..models import Hashtag


@login_required
def mentions_search(request):
    q = request.GET.get('q', '').strip()
    results = []

    if q:
        candidatos = User.objects.filter(username__istartswith=q).exclude(id=request.user.id)

        ids_relacionados = set(
            Follow.objects.filter(
                Q(follower=request.user) | Q(followed=request.user)
            ).values_list('follower_id', 'followed_id').distinct()
        )
        ids_relacionados = {
            uid for par in ids_relacionados for uid in par if uid != request.user.id
        }

        usuarios = list(candidatos.order_by('username'))
        usuarios.sort(key=lambda u: (u.id not in ids_relacionados, u.username.lower()))

        results = [{'username': u.username} for u in usuarios[:10]]

    return JsonResponse({'results': results})


@login_required
def hashtags_search(request):
    q = request.GET.get('q', '').strip()
    results = []

    if q:
        # Solo de publicaciones visibles: el nombre también puede ser un spoiler.
        tags = Hashtag.objects.visibles_para(request.user).filter(name__istartswith=q).order_by('name')[:10]
        results = [{'name': t.name} for t in tags]

    return JsonResponse({'results': results})


@login_required
def suggested_hashtags(request):
    tags = Hashtag.objects.visibles_para(request.user).order_by('-num_posts', 'name')[:10]

    return JsonResponse({
        'results': [t.name for t in tags]
    })