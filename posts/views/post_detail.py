from django.shortcuts import get_object_or_404, render

from ..models import Post


def post_detail_react_view(request, post_id):
    """Monta React para el detalle de post. Sin login: visible_for() filtra
    igual a usuarios autenticados y anónimos."""
    get_object_or_404(Post.objects.visible_for(request.user), id=post_id)
    return render(request, 'posts/post_detail_react.html', {'post_id': post_id})