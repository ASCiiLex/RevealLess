from django.shortcuts import redirect


def hashtag_detail(request, name):
    return redirect(f'/feed/?hashtag={name}')