from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
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


def logout_view(request):
    logout(request)
    return redirect('login')