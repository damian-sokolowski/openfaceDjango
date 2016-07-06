from django.shortcuts import render
from django.http import HttpResponse
from webopenface.models import Person, DetectedPeople, DetectedFace, Frame


def index(request):
    added_people = Person.objects.order_by('name')
    context = {'added_people': added_people}
    return render(request, 'webopenface/index.html', context)


def preview(request):
    detected_people = []
    latest_frame = Frame.objects.latest('add_date')
    context = {
        'latest_frame': latest_frame
    }
    return render(request, 'webopenface/preview.html', context)


def person(request):
    return render(request, 'webopenface/person.html')


def last_frames(request):
    frames = Frame.objects.order_by('-add_date')[:10]
    return render(request, 'webopenface/lastframes.html', {'frames': frames})


def detected_people(request, pk):
    detected = Frame.objects.get(pk=pk).detectedface_set.all()
    context = {
        'detected': detected
    }
    return render(request, 'webopenface/detected_people.html', context)
