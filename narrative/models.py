from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from core.validators import validate_image_size


def obra_image_path(instance, filename):
    return f'narrative/obras/{instance.slug}/{filename}'


def unidad_image_path(instance, filename):
    return f'narrative/unidades/{instance.obra.slug}/{filename}'


class Categoria(models.Model):
    """Etiqueta cosmética compartida entre obras (ej. 'anime', 'series',
    'películas', 'novelas'). Puramente de búsqueda/filtro — no participa
    en frontera_orden ni en ninguna regla de visibilidad, igual criterio
    que FamiliaNarrativa en posts/comments."""

    nombre = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'

    def __str__(self):
        return self.nombre


class Obra(models.Model):
    TIPO_SERIE = 'serie'
    TIPO_PELICULA = 'pelicula'
    TIPO_ESPECIAL = 'especial'
    TIPO_OVA = 'ova'
    TIPO_CORTO = 'corto'
    TIPO_MANGA = 'manga'
    TIPO_CHOICES = [
        (TIPO_SERIE, 'Serie'),
        (TIPO_PELICULA, 'Película'),
        (TIPO_ESPECIAL, 'Especial de TV'),
        (TIPO_OVA, 'OVA'),
        (TIPO_CORTO, 'Corto'),
        (TIPO_MANGA, 'Manga'),
    ]

    titulo = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default=TIPO_SERIE)
    sinopsis = models.TextField(blank=True)
    fecha_publicacion = models.DateField(null=True, blank=True)
    # Varios nombres separados por coma. Sin modelo Autor propio: es
    # metadato cosmético, igual criterio pragmático que SQLite para el MVP.
    autor = models.CharField(max_length=200, blank=True)
    imagen = models.ImageField(
        upload_to=obra_image_path,
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp']),
            validate_image_size,
        ],
    )
    categorias = models.ManyToManyField(Categoria, blank=True, related_name='obras')

    # Vínculo puramente informativo entre continuidades de una misma
    # franquicia (ej. anime -> manga, película -> libro). No participa en
    # frontera_orden ni en visible_for(): cada continuidad sigue siendo
    # una isla de progreso independiente. Mismo criterio que Categoria.
    adapta_a = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='adaptaciones',
        help_text='Obra origen si esta es una adaptación de otra continuidad (ej. anime → manga).',
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
    # Real (Fase A, episodios vía Jikan) o aproximada (Fase B, capítulos de
    # manga por fecha de volumen). null mientras no se conozca ninguna de
    # las dos.
    fecha = models.DateField(null=True, blank=True)
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


class ExternalId(models.Model):
    """Ancla entre una entidad propia y su identificador en una fuente
    externa. Permite reimportar sin duplicar (Fase A) y que Fase B
    localice Obra y episodios ya importados por su MAL ID."""

    SOURCE_JIKAN = 'jikan'
    SOURCE_CHOICES = [(SOURCE_JIKAN, 'Jikan (MyAnimeList)')]

    source = models.CharField(max_length=30, choices=SOURCE_CHOICES)
    external_id = models.CharField(max_length=50)
    obra = models.ForeignKey(Obra, on_delete=models.CASCADE, null=True, blank=True, related_name='external_ids')
    unidad = models.ForeignKey(UnidadNarrativa, on_delete=models.CASCADE, null=True, blank=True, related_name='external_ids')

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(Q(obra__isnull=False) & Q(unidad__isnull=True))
                    | (Q(obra__isnull=True) & Q(unidad__isnull=False)),
                name='externalid_un_solo_destino',
            ),
            models.UniqueConstraint(fields=['source', 'obra'], name='uniq_source_obra', condition=Q(obra__isnull=False)),
            models.UniqueConstraint(fields=['source', 'unidad'], name='uniq_source_unidad', condition=Q(unidad__isnull=False)),
        ]

    def __str__(self):
        return f'{self.source}:{self.external_id}'


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
    Único' en El Señor de los Anillos), o una minihistoria (portadas que
    cuentan una historia en paralelo, publicadas dentro de capítulos ya
    existentes). Es una etiqueta de agrupación y suscripción: no participa
    en el cálculo de frontera_orden. Cada post sigue calculando su propia
    frontera vía referencia_narrativa/frontera_spoiler, exactamente igual
    que sin tema.

    Vive en narrative (no en subscriptions) porque es una propiedad de la
    obra, igual que UnidadNarrativa — no del acto de suscribirse a ella."""

    TIPO_TEMATICO = 'tematico'
    TIPO_MINIHISTORIA = 'minihistoria'
    TIPO_CHOICES = [
        (TIPO_TEMATICO, 'Temático'),
        (TIPO_MINIHISTORIA, 'Minihistoria'),
    ]

    obra = models.ForeignKey(Obra, on_delete=models.CASCADE, related_name='temas_transversales')
    nombre = models.CharField(max_length=150)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default=TIPO_TEMATICO)
    # Solo se usa para minihistorias: capítulos/episodios concretos en los
    # que aparece una página/escena de este hilo. No implica pertenencia
    # narrativa — cada unidad conserva su propio padre y su propia frontera.
    unidades = models.ManyToManyField(UnidadNarrativa, blank=True, related_name='temas_transversales')

    class Meta:
        unique_together = ('obra', 'nombre')
        ordering = ['nombre']

    def __str__(self):
        return f'{self.obra.titulo} · {self.nombre}'


class SolicitudTema(models.Model):
    """Propuesta de un usuario para crear un TemaTransversal nuevo en una
    obra. No crea el tema directamente — requiere aprobación explícita
    (vía acción de admin), que entonces sí crea el TemaTransversal real.
    Mismo criterio de 'admin como última instancia' que ya se usa con
    frontera_origen=admin en ClasificacionNarrativa."""

    ESTADO_PENDIENTE = 'pendiente'
    ESTADO_APROBADA = 'aprobada'
    ESTADO_RECHAZADA = 'rechazada'
    ESTADO_CHOICES = [
        (ESTADO_PENDIENTE, 'Pendiente'),
        (ESTADO_APROBADA, 'Aprobada'),
        (ESTADO_RECHAZADA, 'Rechazada'),
    ]

    obra = models.ForeignKey(Obra, on_delete=models.CASCADE, related_name='solicitudes_tema')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='solicitudes_tema')
    nombre = models.CharField(max_length=150)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default=ESTADO_PENDIENTE)
    creado_en = models.DateTimeField(auto_now_add=True)
    resuelto_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-creado_en']

    def __str__(self):
        return f'{self.usuario.username} propone "{self.nombre}" en {self.obra.titulo} ({self.estado})'


class ClasificacionNarrativa(models.Model):
    """Mixin abstracto compartido por Post y Comment. frontera_orden es el
    valor principal que consulta el motor de visibilidad.

    obra_cruzada / frontera_cruzada cubren el caso de contenido que vive
    en una obra (ej. anime) pero revela información cuya frontera real
    está en otra continuidad de la misma franquicia (ej. manga). Cuando
    están informados, el motor exige ADEMÁS progreso suficiente en
    obra_cruzada. Es declarativo (usuario o IA), nunca automático, y no
    implica ningún mapeo de equivalencia capítulo↔episodio entre las dos
    obras — cada una sigue con su propia escala de orden.

    emocion_autor: la emoción que el propio autor declara sentir sobre su
    contenido narrativo, distinta y separada de PostReaction/
    CommentReaction (reacciones de otros usuarios al contenido). Siempre
    opcional. No participa en frontera_orden ni en visible_for() -- es
    puramente expresivo."""

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

    EMOCION_ME_GUSTA = 'me_gusta'
    EMOCION_ME_ENCANTA = 'me_encanta'
    EMOCION_ME_DIVIERTE = 'me_divierte'
    EMOCION_ME_SORPRENDE = 'me_sorprende'
    EMOCION_ME_ENFADA = 'me_enfada'
    EMOCION_ME_DA_ASCO = 'me_da_asco'
    EMOCION_ME_ENTRISTECE = 'me_entristece'
    EMOCION_ME_ENTUSIASMA = 'me_entusiasma'
    EMOCION_ME_EMOCIONA = 'me_emociona'
    EMOCION_ME_DA_CURIOSIDAD = 'me_da_curiosidad'
    EMOCION_ME_DA_MIEDO = 'me_da_miedo'
    EMOCION_CHOICES = [
        (EMOCION_ME_GUSTA, 'Me gusta'),
        (EMOCION_ME_ENCANTA, 'Me encanta'),
        (EMOCION_ME_DIVIERTE, 'Me divierte'),
        (EMOCION_ME_SORPRENDE, 'Me sorprende'),
        (EMOCION_ME_ENFADA, 'Me enfada'),
        (EMOCION_ME_DA_ASCO, 'Me da asco'),
        (EMOCION_ME_ENTRISTECE, 'Me entristece'),
        (EMOCION_ME_ENTUSIASMA, 'Me entusiasma'),
        (EMOCION_ME_EMOCIONA, 'Me emociona'),
        (EMOCION_ME_DA_CURIOSIDAD, 'Me da curiosidad'),
        (EMOCION_ME_DA_MIEDO, 'Me da miedo'),
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

    emocion_autor = models.CharField(
        max_length=20, choices=EMOCION_CHOICES, null=True, blank=True,
    )

    # Frontera cruzada entre continuidades (opcional, MVP del blindaje).
    obra_cruzada = models.ForeignKey(
        Obra, on_delete=models.PROTECT, null=True, blank=True,
        related_name='%(class)s_cruzados',
        help_text='Obra distinta (ej. manga si esto es del anime) cuya frontera también debe cumplirse.',
    )
    frontera_cruzada = models.ForeignKey(
        UnidadNarrativa, on_delete=models.PROTECT, null=True, blank=True,
        related_name='%(class)s_frontera_cruzada',
        help_text='Punto de obra_cruzada hasta el que hay que haber llegado.',
    )
    frontera_cruzada_orden = models.PositiveIntegerField(null=True, blank=True, editable=False)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.frontera_origen == self.ORIGEN_HEREDADO_POST:
            self.frontera_orden = None
        elif self.frontera_spoiler_id:
            self.frontera_orden = self.frontera_spoiler.orden_fin

        self.frontera_cruzada_orden = (
            self.frontera_cruzada.orden_fin if self.frontera_cruzada_id else None
        )

        super().save(*args, **kwargs)