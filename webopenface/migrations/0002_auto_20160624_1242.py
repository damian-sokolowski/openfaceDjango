# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-06-24 12:42
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webopenface', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='person',
            name='uid',
            field=models.CharField(blank=True, max_length=50),
        ),
    ]