from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from follows.models import Follow
from profiles.models import Profile
from .forms import ProfileForm


# 🔹 PERFIL
def profile_view(request, username):
    # Usuario
    profile_user = get_object_or_404(User, username=username)

    # Perfil (optimizado)
    profile = get_object_or_404(
        Profile.objects.select_related('user'),
        user=profile_user
    )

    # Posts (optimizado)
    posts = profile_user.posts.all().select_related('author')

    # Follow state
    is_following = False
    if request.user.is_authenticated and request.user != profile_user:
        is_following = Follow.objects.filter(
            follower=request.user,
            followed=profile_user
        ).exists()

    # Contadores
    followers_count = Follow.objects.filter(
        followed=profile_user
    ).count()

    following_count = Follow.objects.filter(
        follower=profile_user
    ).count()

    # Guardados
    saved_posts_ids = []
    if request.user.is_authenticated:
        saved_posts_ids = list(
            request.user.saved_posts.values_list('post_id', flat=True)
        )

    context = {
        'profile_user': profile_user,
        'profile': profile,
        'posts': posts,
        'is_following': is_following,
        'followers_count': followers_count,
        'following_count': following_count,
        'saved_posts_ids': saved_posts_ids,
    }

    return render(request, 'profiles/profile.html', context)


# 🔹 SEARCH
def search_view(request):
    query = request.GET.get("q", "").strip()
    results = []

    if query:
        results = User.objects.select_related('profile').filter(
            Q(username__icontains=query) |
            Q(profile__bio__icontains=query)
        ).distinct()

    return render(request, 'profiles/search.html', {
        'query': query,
        'results': results,
    })


# 🔹 FOLLOWERS
def followers_view(request, username):
    profile_user = get_object_or_404(User, username=username)

    followers = Follow.objects.filter(
        followed=profile_user
    ).select_related('follower', 'follower__profile')

    return render(request, "follows/followers_list.html", {
        "profile_user": profile_user,
        "followers": followers,
    })


# 🔹 FOLLOWING
def following_view(request, username):
    profile_user = get_object_or_404(User, username=username)

    following = Follow.objects.filter(
        follower=profile_user
    ).select_related('followed', 'followed__profile')

    return render(request, "follows/following_list.html", {
        "profile_user": profile_user,
        "following": following,
    })


# 🔹 EDIT PROFILE
@login_required
def edit_profile(request):
    # 🔥 seguridad extra (aunque debería existir siempre)
    profile = getattr(request.user, 'profile', None)

    if not profile:
        profile = Profile.objects.create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(
            request.POST,
            request.FILES,
            instance=profile,
            user=request.user
        )

        if form.is_valid():
            form.save(request.user)
            return redirect('profile', username=request.user.username)

    else:
        form = ProfileForm(
            instance=profile,
            user=request.user
        )

    return render(request, 'profiles/edit_profile.html', {
        'form': form
    })