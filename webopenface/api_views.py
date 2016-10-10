from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from openFaceClass import OpenFaceClass
from webopenface.models import Person, RecognizedPeople, Frame

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
            latest_frame = Frame.objects.latest('add_date')
            respons_data['type'] = "PREVIEW_FRAME"
            respons_data['dataURL'] = latest_frame.frame
            respons_data['publishedRecently'] = latest_frame.was_published_recently()
            respons_data['recognizedPeople'] = open_face.recently_recognized()
        else:
            print("Warning: Unknown message type: {}".format(msg['type']))

        return HttpResponse(json.dumps(respons_data), content_type="application/json")

    return render(
        request,
        'webopenface/base.html',
        {
            'preview_list': RecognizedPeople.objects.order_by('face__frame__add_date')
        }
    )


def one_time_startup():
    global open_face
    open_face = OpenFaceClass()
    open_face.loadData()
