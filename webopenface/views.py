from django.shortcuts import render
from django.http import HttpResponse
from webopenface.models import DetectedPeople, DetectedFace


def index(request):
    preview_list = DetectedPeople.objects.order_by('face__frame__add_date')
    output = ', '.join(i.person.name for i in preview_list)
    return HttpResponse(output)


def preview(request):
    return HttpResponse("Hello, world. preview")


def person(request):
    return HttpResponse("Hello, world. person")
