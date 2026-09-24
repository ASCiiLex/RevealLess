from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def saved_posts_react_view(request):
    """Monta React para Guardados."""
    return render(request, 'saved_posts/saved_posts_react.html')