from django.contrib.auth import logout
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST


@require_POST
def logout_view(request):
    # Solo POST: un GET (enlace o imagen externa) no debe cerrar la sesión.
    logout(request)
    return HttpResponse(status=204)


@ensure_csrf_cookie
def login_react_view(request):
    """Monta React para el login. ensure_csrf_cookie: la página no renderiza
    {% csrf_token %}, así que sin él el POST desde React fallaría por CSRF."""
    if request.user.is_authenticated:
        return redirect('feed_react')
    return render(request, 'accounts/login_react.html')


@ensure_csrf_cookie
def register_react_view(request):
    if request.user.is_authenticated:
        return redirect('feed_react')
    return render(request, 'accounts/register_react.html')