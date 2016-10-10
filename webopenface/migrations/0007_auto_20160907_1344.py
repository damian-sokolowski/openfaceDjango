# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webopenface', '0006_auto_20160804_0835'),
    ]

    operations = [
        migrations.CreateModel(
            name='RecognizedPeople',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('probability', models.SmallIntegerField(default=0)),
                ('add_date', models.DateTimeField(auto_now_add=True)),
                ('face', models.ForeignKey(to='webopenface.DetectedFace')),
                ('person', models.ForeignKey(to='webopenface.Person', null=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='detectedpeople',
            name='face',
        ),
        migrations.RemoveField(
            model_name='detectedpeople',
            name='person',
        ),
        migrations.DeleteModel(
            name='DetectedPeople',
        ),
    ]
