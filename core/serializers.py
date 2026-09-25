def serializar_reactores(request, reacciones):
    """Usuarios que reaccionaron: nombre, enlace al perfil React, avatar
    absoluto y emoción, del más reciente al más antiguo."""
    usuarios = []
    for reaccion in reacciones.select_related('user', 'user__profile').order_by('-created_at'):
        user = reaccion.user
        avatar = (
            user.profile.image_url
            if hasattr(user, 'profile')
            else '/static/img/default_profile.jpg'
        )
        usuarios.append({
            'username': user.username,
            'profile_url': f'/perfil/{user.username}/',
            'avatar_url': request.build_absolute_uri(avatar),
            'reaction': reaccion.reaction,
        })
    return usuarios