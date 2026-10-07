import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0011_post_parte_opcional_modo_cruce'),
    ]

    operations = [
        migrations.AddField(
            model_name='postimagen',
            name='enfoque_x',
            field=models.PositiveSmallIntegerField(
                default=50, validators=[django.core.validators.MaxValueValidator(100)],
            ),
        ),
        migrations.AddField(
            model_name='postimagen',
            name='enfoque_y',
            field=models.PositiveSmallIntegerField(
                default=50, validators=[django.core.validators.MaxValueValidator(100)],
            ),
        ),
        migrations.AddField(
            model_name='postimagen',
            name='zoom',
            field=models.PositiveSmallIntegerField(
                default=100,
                validators=[
                    django.core.validators.MinValueValidator(100),
                    django.core.validators.MaxValueValidator(300),
                ],
            ),
        ),
    ]