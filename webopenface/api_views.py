from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from openFaceClass import OpenFaceClass
from tornado_websockets.websocket import WebSocket
from webopenface.models import Person, DetectedPeople, PeopleFace, Frame

import json

open_face = None

@csrf_exempt
def on_message(request):
    global open_face
    if request.method == 'POST':
        msg = json.loads(request.body)
        respons_data = {}
        if msg['type'] == 'ADD_PERSON':
            respons_data['type'] = 'ADD_PERSON'
            person_name = msg['val']
            if msg['val'] != '':
                p = Person(name=person_name)
                p.save()
                respons_data['type'] = 'ADD_PERSON'
                respons_data['id'] = open_face.addPerson(p.pk)

        elif msg['type'] == 'TRAIN_SVM':
            open_face.trainSVM()
        elif msg['type'] == 'FRAME':
            respons_data = open_face.processFrame(msg['dataURL'], msg['identity'], msg['training'])
        elif msg['type'] == 'GET_FRAME':
            detected_people = []
            latest_frame = Frame.objects.latest('add_date')
            published_recently = latest_frame.was_published_recently()
            for face in latest_frame.detectedface_set.all():
                for detected_person in face.detectedpeople_set.all():
                    detected_people.append([detected_person.person.name, detected_person.probability])
            respons_data['type'] = "PREVIEW_FRAME"
            respons_data['dataURL'] = latest_frame.frame
            respons_data['publishedRecently'] = published_recently
            respons_data['detectedPeople'] = detected_people
            print
        else:
            print("Warning: Unknown message type: {}".format(msg['type']))

        return HttpResponse(json.dumps(respons_data), content_type="application/json")

    return render(
        request,
        'webopenface/base.html',
        {
            'preview_list': DetectedPeople.objects.order_by('face__frame__add_date')
        }
    )


def one_time_startup():
    global open_face
    open_face = OpenFaceClass()
    open_face.loadData()
