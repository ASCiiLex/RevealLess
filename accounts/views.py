from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit
from .forms import RegisterForm


@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)

            user.set_password(form.cleaned_data['password'])
            user.save()

            profile = user.profile

            if form.cleaned_data.get('image'):
                profile.image = form.cleaned_data['image']

            profile.save()

            login(request, user)
            return redirect('feed')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


@ratelimit(key='ip', rate='10/m', method='POST', block=True)
def login_view(request):
    error = None

    if request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST.get('username'),
            password=request.POST.get('password')
        )

        if user:
            login(request, user)
            return redirect('feed')
        else:
            error = "Usuario o contraseña incorrectos"

    return render(request, 'accounts/login.html', {'error': error})


@require_POST
def logout_view(request):
    # Solo POST: un GET (enlace o imagen externa) no debe cerrar la sesión.
    logout(request)
    return HttpResponse(status=204)


@ensure_csrf_cookie
def login_react_view(request):
    """Vista mínima que monta el punto de entrada de React para el login
    (Fase 4). No reemplaza login_view: convive con la vista HTML
    heredada. ensure_csrf_cookie es necesario porque esta página no
    renderiza {% csrf_token %} en ningún <form> Django -- sin el
    decorador, un visitante anónimo nunca recibiría la cookie
    csrftoken, y el POST desde React fallaría por CSRF."""
    if request.user.is_authenticated:
        return redirect('feed_react')
    return render(request, 'accounts/login_react.html')


@ensure_csrf_cookie
def register_react_view(request):
    if request.user.is_authenticated:
        return redirect('feed_react')
    return render(request, 'accounts/register_react.html')