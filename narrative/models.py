from django.db import models
from django.contrib.auth.models import User


class Obra(models.Model):
    TIPO_CHOICES = [
        ('serie', 'Serie'),
    ]

    titulo = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='serie')
    sinopsis = models.TextField(blank=True)

    class Meta:
        ordering = ['titulo']

    def __str__(self):
        return self.titulo

    def recalcular_orden(self):
        """Recalcula orden_inicio/orden_fin de todas sus unidades narrativas.
        orden_manual es un índice de inserción (1-based) sobre la secuencia
        final, no un valor absoluto: el resto de hojas se renumera a su
        alrededor sin huecos ni colisiones."""
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

        # Empate en el índice pedido: gana quien aparece antes en el DFS natural.
        manuales.sort(key=lambda u: (u.orden_manual, hojas_dfs.index(u)))

        secuencia = list(automaticas)
        for unidad in manuales:
            total = len(secuencia) + 1
            indice = min(max(unidad.orden_manual, 1), total)
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

    orden_inicio = models.PositiveIntegerField(editable=False, default=0)
    orden_fin = models.PositiveIntegerField(editable=False, default=0)

    # Índice de inserción (1-based) en la secuencia final. Solo tiene efecto
    # en hojas; en nodos intermedios se ignora durante el recálculo.
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