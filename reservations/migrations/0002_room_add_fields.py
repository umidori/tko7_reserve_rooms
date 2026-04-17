from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reservations', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='room',
            name='building',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='建物'),
        ),
        migrations.AddField(
            model_name='room',
            name='floor',
            field=models.IntegerField(blank=True, null=True, verbose_name='階数'),
        ),
        migrations.AddField(
            model_name='room',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='利用可能'),
        ),
        migrations.AlterField(
            model_name='room',
            name='name',
            field=models.CharField(max_length=100, unique=True, verbose_name='室名'),
        ),
        migrations.AlterField(
            model_name='room',
            name='capacity',
            field=models.PositiveIntegerField(verbose_name='収容人数'),
        ),
    ]
