def sala_chat(usuario_a, usuario_b):
    """Grupo de Channels de una conversación: mismo nombre sea cual sea el orden de los participantes."""
    primero, segundo = sorted([usuario_a, usuario_b])
    return f'chat_{primero}_{segundo}'