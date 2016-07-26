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
