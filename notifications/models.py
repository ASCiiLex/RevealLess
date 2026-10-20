from django.db import models
from django.contrib.auth.models import User

# Código guardado en BD -> texto que se muestra al usuario.
VERBOS_TEXTO = {
    'commented': 'comentó tu publicación',
    'replied': 'respondió a tu comentario',
    'mentioned': 'te ha mencionado en un comentario',
}
TIPOS_DE_COMENTARIO = ('comment', 'reply')


class Notification(models.Model):
    actor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications_sent',
        verbose_name='Autor de la acción',
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Destinatario',
    )

    # Un código de VERBOS_TEXTO o un texto ya redactado (sugerencias de obra).
    verb = models.CharField(max_length=255, verbose_name='Acción')

    target_type = models.CharField(
        max_length=20,
        choices=[
            ('post', 'Publicación'),
            ('comment', 'Comentario'),
            ('reply', 'Respuesta'),
            ('follow', 'Seguimiento'),
            ('message', 'Mensaje'),
            ('obra', 'Obra'),
        ],
        verbose_name='Tipo de objetivo',
    )

    target_id = models.IntegerField(null=True, blank=True, verbose_name='ID del objetivo')

    reaction = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name='Reacción',
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')

    seen = models.BooleanField(default=False, verbose_name='Vista')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'

    def __str__(self):
        return f"{self.actor.username} {self.verb}"

    @staticmethod
    def precargar_posts(notificaciones):
        """Resuelve el post de todas las notificaciones con dos consultas en vez de una por notificación."""
        from comments.models import Comment
        from posts.models import Post

        notificaciones = list(notificaciones)
        ids_post = {n.target_id for n in notificaciones if n.target_type == 'post' and n.target_id}
        ids_comentario = {n.target_id for n in notificaciones if n.target_type in TIPOS_DE_COMENTARIO and n.target_id}
        post_de_comentario = (
            dict(Comment.objects.filter(id__in=ids_comentario).values_list('id', 'post_id'))
            if ids_comentario else {}
        )
        posts = Post.objects.only('id', 'image').in_bulk(ids_post | set(post_de_comentario.values()))
        for n in notificaciones:
            if n.target_type == 'post':
                n._post_cache = posts.get(n.target_id)
            elif n.target_type in TIPOS_DE_COMENTARIO:
                n._post_cache = posts.get(post_de_comentario.get(n.target_id))
        return notificaciones

    @property
    def verb_display(self):
        """Texto en español del verbo; si no es un código conocido, se devuelve tal cual."""
        if self.verb == 'reacted':
            objetivo = 'comentario' if self.target_type in TIPOS_DE_COMENTARIO else 'publicación'
            return f'reaccionó a tu {objetivo}'
        return VERBOS_TEXTO.get(self.verb, self.verb)

    @property
    def avatar(self):
        if hasattr(self.actor, "profile") and self.actor.profile.image:
            return self.actor.profile.image.url
        return "/static/img/default_profile.jpg"

    @property
    def _related_post(self):
        # Cachea la query: post_thumbnail y url no piden dos veces el mismo Post.
        # target_id es un Post si target_type='post', un Comment si 'comment'/'reply'.
        if not hasattr(self, "_post_cache"):
            self._post_cache = None
            if self.target_id:
                from posts.models import Post
                posts = Post.objects.only("id", "image")
                if self.target_type == "post":
                    self._post_cache = posts.filter(id=self.target_id).first()
                elif self.target_type in TIPOS_DE_COMENTARIO:
                    self._post_cache = posts.filter(comments__id=self.target_id).first()
        return self._post_cache

    @property
    def post_thumbnail(self):
        post = self._related_post
        if post and post.image:
            return post.image_url
        return "/static/img/default_post.jpg"

    @property
    def url(self):
        # Todas las rutas apuntan a las vistas React (Fase 4).
        if self.target_type in ("post", *TIPOS_DE_COMENTARIO):
            post = self._related_post
            if post:
                return f"/posts/{post.id}/"
            return f"/notificaciones/post-no-existe/{self.id}/"

        if self.target_type == "follow":
            return f"/perfil/{self.actor.username}/"

        if self.target_type == "message":
            return f"/mensajes/{self.actor.username}/"

        if self.target_type == "obra":
            # Sugerencia aprobada: a la obra. Rechazada (sin obra): al feed.
            from narrative.models import Obra
            slug = Obra.objects.filter(id=self.target_id).values_list('slug', flat=True).first() if self.target_id else None
            return f"/narrative/obra/{slug}/" if slug else "/feed/"

        return "#"