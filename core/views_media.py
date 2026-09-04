from django.views.static import serve
from django.conf import settings

def media_serve(request, path):
    return serve(request, path, document_root=settings.MEDIA_ROOT)