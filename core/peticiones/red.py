from ipaddress import ip_address

# Las fija Cloudflare (delante de Render) con la IP real; Render las recomienda para esto.
# X-Forwarded-For no sirve: Render añade al final y el cliente controla el principio.
CABECERAS_IP_CLIENTE = ('HTTP_TRUE_CLIENT_IP', 'HTTP_CF_CONNECTING_IP')


def ip_cliente(request):
    """IP para el rate limit por IP. Sin esas cabeceras (en local), la de la conexión."""
    for cabecera in CABECERAS_IP_CLIENTE:
        valor = request.META.get(cabecera, '').strip()
        try:
            return str(ip_address(valor))
        except ValueError:
            continue
    return request.META['REMOTE_ADDR']