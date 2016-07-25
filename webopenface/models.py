from __future__ import unicode_literals
from django.db import models


class Person(models.Model):
    uid = models.CharField(max_length=50, blank=True)
    name = models.CharField(max_length=50, )
    add_date = models.DateTimeField(auto_now_add=False, )
    mod_date = models.DateTimeField(auto_now=False, )

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
    add_date = models.DateTimeField(auto_now_add=False, )

    def __unicode__(self):
        return self.frame


class DetectedFace(models.Model):
    frame = models.ForeignKey(Frame)
    face = models.TextField()

    def __unicode__(self):
        return self.face


class DetectedPeople(models.Model):
    face = models.ForeignKey(DetectedFace, )
    person = models.ForeignKey(Person, )

    def __unicode__(self):
        return self.person.name
