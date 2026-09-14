from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('narrative', '0006_solicitudtema'),
    ]

    operations = [
        migrations.AddField(
            model_name='obra',
            name='adapta_a',
            field=models.ForeignKey(
                blank=True,
                help_text='Obra origen si esta es una adaptación de otra continuidad (ej. anime → manga).',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='adaptaciones',
                to='narrative.obra',
            ),
        ),
    ]