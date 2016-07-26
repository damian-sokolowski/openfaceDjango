from django.shortcuts import render
from webopenface.models import Person, Frame


def index(request):
    return render(
        request,
        'webopenface/index.html',
        {
            'added_people': Person.objects.order_by('name')
        }
    )


def preview(request):
    return render(
        request,
        'webopenface/preview.html',
        {
            'latest_frame': Frame.objects.latest('add_date')
        }
    )


def person(request):
    return render(request, 'webopenface/person.html')


def last_frames(request):
    return render(
        request,
        'webopenface/last_frames.html',
        {
            'frames': Frame.objects.order_by('-add_date').all()
        }
    )


def detected_people(request, pk):
    return render(
        request,
        'webopenface/detected_people.html',
        {
            'detected': Frame.objects.get(pk=pk).detectedface_set[:1000]
        }
    )


def added_people(request):
    return render(
        request,
        'webopenface/added_people.html',
        {
            'people': Person.objects.order_by('-add_date').all()
        }
    )


def person_details(request, pk):
    return render(
        request,
        'webopenface/person_details.html',
        {
            'person': Person.objects.get(pk=pk)
        }
    )
