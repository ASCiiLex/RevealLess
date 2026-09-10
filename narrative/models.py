from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from core.validators import validate_image_size


def obra_image_path(instance, filename):
    return f'narrative/obras/{instance.slug}/{filename}'


def unidad_image_path(instance, filename):
    return f'narrative/unidades/{instance.obra.slug}/{filename}'


class Obra(models.Model):
    TIPO_CHOICES = [
        ('serie', 'Serie'),
    ]

    titulo = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='serie')
    sinopsis = models.TextField(blank=True)
    imagen = models.ImageField(
        upload_to=obra_image_path,
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp']),
            validate_image_size,
        ],
    )

    class Meta:
        ordering = ['titulo']

    def __str__(self):
        return self.titulo

    @property
    def image_url(self):
        try:
            if self.imagen and hasattr(self.imagen, 'url'):
                return self.imagen.url
        except ValueError:
            pass
        return '/static/img/default_post.jpg'

    def recalcular_orden(self):
        """Recalcula orden_inicio/orden_fin de todas sus unidades narrativas.
        orden_manual es un índice de inserción (1-based) sobre la secuencia
        final, no un valor absoluto: el resto de hojas se renumera a su
        alrededor sin huecos ni colisiones. Empates en el mismo índice se
        desempatan por orden de aparición en el DFS natural."""
        unidades = list(self.unidades.all())
        por_padre = {}
        for u in unidades:
            por_padre.setdefault(u.padre_id, []).append(u)
        for hijos in por_padre.values():
            hijos.sort(key=lambda u: u.orden_local)

        hojas_dfs = []

        def recorrer(unidad):
            hijos = por_padre.get(unidad.id, [])
            if not hijos:
                hojas_dfs.append(unidad)
                return
            for hijo in hijos:
                recorrer(hijo)

        for raiz in por_padre.get(None, []):
            recorrer(raiz)

        manuales = [u for u in hojas_dfs if u.orden_manual is not None]
        automaticas = [u for u in hojas_dfs if u.orden_manual is None]

        manuales.sort(key=lambda u: (u.orden_manual, hojas_dfs.index(u)))

        secuencia = list(automaticas)
        usados = {}
        for unidad in manuales:
            base = unidad.orden_manual + usados.get(unidad.orden_manual, 0)
            usados[unidad.orden_manual] = usados.get(unidad.orden_manual, 0) + 1
            total = len(secuencia) + 1
            indice = min(max(base, 1), total)
            secuencia.insert(indice - 1, unidad)

        posiciones = {u.id: i + 1 for i, u in enumerate(secuencia)}
        resultados = {}

        def calcular_rango(unidad):
            hijos = por_padre.get(unidad.id, [])
            if not hijos:
                pos = posiciones[unidad.id]
                resultados[unidad.id] = (pos, pos)
                return pos, pos
            inicios, fines = [], []
            for hijo in hijos:
                ini, fin = calcular_rango(hijo)
                inicios.append(ini)
                fines.append(fin)
            rango = (min(inicios), max(fines))
            resultados[unidad.id] = rango
            return rango

        for raiz in por_padre.get(None, []):
            calcular_rango(raiz)

        for unidad in unidades:
            ini, fin = resultados.get(unidad.id, (unidad.orden_inicio, unidad.orden_fin))
            if unidad.orden_inicio != ini or unidad.orden_fin != fin:
                UnidadNarrativa.objects.filter(pk=unidad.pk).update(
                    orden_inicio=ini, orden_fin=fin
                )


class UnidadNarrativa(models.Model):
    obra = models.ForeignKey(Obra, on_delete=models.CASCADE, related_name='unidades')
    padre = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.CASCADE, related_name='hijos'
    )
    tipo = models.CharField(max_length=50)
    nombre = models.CharField(max_length=200)
    orden_local = models.PositiveIntegerField()
    imagen = models.ImageField(
        upload_to=unidad_image_path,
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp']),
            validate_image_size,
        ],
    )

    orden_inicio = models.PositiveIntegerField(editable=False, default=0)
    orden_fin = models.PositiveIntegerField(editable=False, default=0)

    orden_manual = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ['orden_inicio']

    def __str__(self):
        return f'{self.obra.titulo} · {self.nombre}'

    @property
    def es_hoja(self):
        return not self.hijos.exists()

    @property
    def etiqueta(self):
        return self.nombre

    @property
    def image_url(self):
        try:
            if self.imagen and hasattr(self.imagen, 'url'):
                return self.imagen.url
        except ValueError:
            pass
        return self.obra.image_url


class ProgresoUsuario(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progresos')
    obra = models.ForeignKey(Obra, on_delete=models.CASCADE, related_name='progresos')
    unidad_actual = models.ForeignKey(UnidadNarrativa, on_delete=models.PROTECT)
    orden_absoluto = models.PositiveIntegerField(editable=False, default=0)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('usuario', 'obra')

    def __str__(self):
        return f'{self.usuario.username} · {self.obra.titulo} · {self.orden_absoluto}'


class TemaTransversal(models.Model):
    """Hilo temático que atraviesa una obra sin anclarse a una unidad
    narrativa concreta (ej. 'Frutas del diablo' en One Piece, 'El Anillo
    Único' en El Señor de los Anillos). Es una etiqueta de agrupación y
    suscripción: no participa en el cálculo de frontera_orden. Cada post
    sigue calculando su propia frontera vía referencia_narrativa/
    frontera_spoiler, exactamente igual que sin tema.

    Vive en narrative (no en subscriptions) porque es una propiedad de la
    obra, igual que UnidadNarrativa — no del acto de suscribirse a ella."""

    obra = models.ForeignKey(Obra, on_delete=models.CASCADE, related_name='temas_transversales')
    nombre = models.CharField(max_length=150)

    class Meta:
        unique_together = ('obra', 'nombre')
        ordering = ['nombre']

    def __str__(self):
        return f'{self.obra.titulo} · {self.nombre}'


class ClasificacionNarrativa(models.Model):
    """Mixin abstracto compartido por Post y Comment. frontera_orden es el
    único valor que debe consultar el motor de visibilidad."""

    ORIGEN_EXPLICITO = 'explicito'
    ORIGEN_IA = 'ia'
    ORIGEN_FALLBACK = 'fallback'
    ORIGEN_HEREDADO_POST = 'heredado_post'
    ORIGEN_ADMIN = 'admin'
    ORIGEN_CHOICES = [
        (ORIGEN_EXPLICITO, 'Explícito'),
        (ORIGEN_IA, 'IA'),
        (ORIGEN_FALLBACK, 'Fallback'),
        (ORIGEN_HEREDADO_POST, 'Heredado del post'),
        (ORIGEN_ADMIN, 'Corrección administrativa'),
    ]

    NIVEL_MENOR = 'menor'
    NIVEL_IMPORTANTE = 'importante'
    NIVEL_TRAMA_CENTRAL = 'trama_central'
    NIVEL_CHOICES = [
        (NIVEL_MENOR, 'Menor'),
        (NIVEL_IMPORTANTE, 'Importante'),
        (NIVEL_TRAMA_CENTRAL, 'Trama central'),
    ]

    referencia_narrativa = models.ForeignKey(
        UnidadNarrativa, on_delete=models.PROTECT,
        related_name='%(class)s_referenciados',
    )
    frontera_spoiler = models.ForeignKey(
        UnidadNarrativa, on_delete=models.PROTECT, null=True, blank=True,
        related_name='%(class)s_frontera',
    )
    frontera_orden = models.PositiveIntegerField(null=True, blank=True, editable=False)
    frontera_origen = models.CharField(max_length=20, choices=ORIGEN_CHOICES)
    nivel_spoiler = models.CharField(max_length=20, choices=NIVEL_CHOICES, default=NIVEL_MENOR)
    ia_confianza = models.FloatField(null=True, blank=True)
    clasificado_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.frontera_origen == self.ORIGEN_HEREDADO_POST:
            self.frontera_orden = None
        elif self.frontera_spoiler_id:
            self.frontera_orden = self.frontera_spoiler.orden_fin
        super().save(*args, **kwargs)