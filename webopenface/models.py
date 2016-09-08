from __future__ import unicode_literals
from django.db import models

import timeCalculation


class Person(models.Model):
    uid = models.CharField(max_length=50, blank=True)
    name = models.CharField(max_length=50, )
    add_date = models.DateTimeField(auto_now_add=True, )
    mod_date = models.DateTimeField(auto_now=True, )

    class Meta:
        verbose_name_plural = "people"

    def __unicode__(self):
        return self.name


class PeopleFace(models.Model):
    person = models.ForeignKey(Person, )
    face = models.TextField()

    def __unicode__(self):
        return self.person.name


class Frame(models.Model):
    frame = models.TextField()
    add_date = models.DateTimeField(auto_now_add=True, )

    def __unicode__(self):
        return self.frame[0:100]

    def was_published_recently(self):
        return self.add_date >= timeCalculation.turn_back_time(0.5)

    def save_delete(self):
        objects = Frame.objects.all()
        if objects.count() >= 2000:
            Frame.objects.filter(id__in=objects[:200]).delete()
        self.save()


class DetectedFace(models.Model):
    frame = models.ForeignKey(Frame)
    face = models.TextField()

    def __unicode__(self):
        return self.face[0:100]


class RecognizedPeople(models.Model):
    face = models.ForeignKey(DetectedFace, )
    person = models.ForeignKey(Person, null=True, blank=True)
    probability = models.SmallIntegerField(default=0)
    add_date = models.DateTimeField(auto_now_add=True, )

    def __unicode__(self):
        return str(self.probability)
