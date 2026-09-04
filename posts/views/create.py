from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from ..forms import PostForm


@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            new_post = form.save(commit=False)
            new_post.author = request.user
            new_post.save()

            # 🔥 REDIRECT A PERFIL
            return redirect('profile', username=request.user.username)

    else:
        form = PostForm()

    return render(request, 'posts/create_post.html', {'form': form})