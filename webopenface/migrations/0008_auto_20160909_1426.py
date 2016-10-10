# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webopenface', '0007_auto_20160907_1344'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recognizedpeople',
            name='person',
            field=models.ForeignKey(blank=True, to='webopenface.Person', null=True),
        ),
    ]
