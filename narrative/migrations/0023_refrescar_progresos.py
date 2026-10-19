from django.db import migrations


def refrescar(apps, schema_editor):
    """Progresos con la posición vigente de su unidad (mismo criterio que calcular_orden_absoluto)."""
    Unidad = apps.get_model('narrative', 'UnidadNarrativa')
    Progreso = apps.get_model('narrative', 'ProgresoUsuario')
    con_hijos = set(Unidad.objects.filter(padre__isnull=False).values_list('padre_id', flat=True))
    for progreso in Progreso.objects.select_related('unidad_actual'):
        unidad = progreso.unidad_actual
        posicion = max(unidad.orden_inicio - 1, 0) if unidad.id in con_hijos else unidad.orden_inicio
        if progreso.orden_absoluto != posicion:
            Progreso.objects.filter(pk=progreso.pk).update(orden_absoluto=posicion)


class Migration(migrations.Migration):

    dependencies = [
        ('narrative', '0022_personaje_identidades'),
    ]

    operations = [
        migrations.RunPython(refrescar, migrations.RunPython.noop),
    ]