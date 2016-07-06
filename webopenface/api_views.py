from django.shortcuts import render
from django.http import HttpResponse
from webopenface.models import Person, DetectedPeople, PeopleFace, Frame
from django.views.decorators.csrf import csrf_exempt

import argparse
import cv2
import imagehash
import json
from PIL import Image
import numpy as np
import os
import StringIO
import urllib
import base64

from sklearn.decomposition import PCA
from sklearn.grid_search import GridSearchCV
from sklearn.grid_search import GridSearchCV
from sklearn.svm import SVC

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.cm as cm

import openface

fileDir = os.path.dirname(os.path.realpath(__file__))

modelDir = os.path.join(fileDir, '..', 'openface', 'models')
dlibModelDir = os.path.join(modelDir, 'dlib')
openfaceModelDir = os.path.join(modelDir, 'openface')


parser = argparse.ArgumentParser()
parser.add_argument('--dlibFacePredictor', type=str, help="Path to dlib's face predictor.",
                    default=os.path.join(dlibModelDir, "shape_predictor_68_face_landmarks.dat"))
parser.add_argument('--networkModel', type=str, help="Path to Torch network model.",
                    default=os.path.join(openfaceModelDir, 'nn4.small2.v1.t7'))
parser.add_argument('--imgDim', type=int,
                    help="Default image dimension.", default=96)
parser.add_argument('--cuda', action='store_true')
parser.add_argument('--unknown', type=bool, default=False,
                    help='Try to predict unknown people')

args = parser.parse_known_args()
#
align = openface.AlignDlib(args[0].dlibFacePredictor)
net = openface.TorchNeuralNet(args[0].networkModel, imgDim=args[0].imgDim,
                              cuda=args[0].cuda)

# unknownImgs = np.load("./openface/examples/web/unknown.npy")
training = False
svm = None

images = {}
people = ()
open_face = None


def face(rep, identity):
    return "{{id: {}, rep[0:5]: {}}}".format(
        str(identity),
        rep[0:5]
    )

@csrf_exempt
def on_message(request):
    global open_face

    global training
    if request.method == 'POST':
        msg = json.loads(request.body)
        respons_data = {}
        if msg['type'] == 'ADD_PERSON':
            respons_data['type'] = 'ADD_PERSON'
            print(msg['val'])
            if msg['val'] != '':
                p = Person(name=msg['val'])
                p.save()
                respons_data['type'] = 'ADD_PERSON'
                respons_data['id'] = p.pk
        elif msg['type'] == 'TRAINING':
            training = msg['val']
        elif msg['type'] == 'FRAME':
            respons_data = open_face.processFrame(msg['dataURL'], msg['identity'], msg['training'])
            print 'cos'
            # respons_data['type'] = "ANNOTATED"
            # respons_data['content'] = msg['dataURL']
        elif msg['type'] == 'GET_FRAME':
            detected_people = []
            latest_frame = Frame.objects.latest('add_date')
            published_recently = latest_frame.was_published_recently()
            for face in latest_frame.detectedface_set.all():
                for detected_person in face.detectedpeople_set.all():
                    detected_people.append(detected_person.person.name)
            respons_data['type'] = "PREVIEW_FRAME"
            respons_data['dataURL'] = latest_frame.frame
            respons_data['publishedRecently'] = published_recently
            respons_data['detectedPeople'] = detected_people
            print
        else:
            print("Warning: Unknown message type: {}".format(msg['type']))

        return HttpResponse(json.dumps(respons_data), content_type="application/json")
    preview_list = DetectedPeople.objects.order_by('face__frame__add_date')
    context = {'preview_list': preview_list}
    return render(request, 'webopenface/base.html', context)


class Face:

    def __init__(self, rep, identity):
        self.rep = rep
        self.identity = identity

    def __repr__(self):
        return "{{id: {}, rep[0:5]: {}}}".format(
            str(self.identity),
            self.rep[0:5]
        )


class OpenFaceServerProtocol:

    def __init__(self):
        self.images = {}
        self.training = True
        self.people = []
        self.svm = None
        if args[0].unknown:
            self.unknownImgs = np.load("./examples/web/unknown.npy")

    def loadData(self):
        pass

    def loadState(self, jsImages, training, jsPeople):
        self.training = training

        for jsImage in jsImages:
            h = jsImage['hash'].encode('ascii', 'ignore')
            self.images[h] = Face(np.array(jsImage['representation']),
                                  jsImage['identity'])

        for jsPerson in jsPeople:
            self.people.append(jsPerson.encode('ascii', 'ignore'))

        if not training:
            self.trainSVM()

    def getData(self):
        X = []
        y = []
        for img in self.images.values():
            X.append(img.rep)
            y.append(img.identity)

        numIdentities = len(set(y + [-1])) - 1
        if numIdentities == 0:
            return None

        if args[0].unknown:
            numUnknown = y.count(-1)
            numIdentified = len(y) - numUnknown
            numUnknownAdd = (numIdentified / numIdentities) - numUnknown
            if numUnknownAdd > 0:
                print("+ Augmenting with {} unknown images.".format(numUnknownAdd))
                for rep in self.unknownImgs[:numUnknownAdd]:
                    # print(rep)
                    X.append(rep)
                    y.append(-1)

        X = np.vstack(X)
        y = np.array(y)
        return (X, y)

    def trainSVM(self):
        print("+ Training SVM on {} labeled images.".format(len(self.images)))
        d = self.getData()
        if d is None:
            self.svm = None
            return
        else:
            (X, y) = d
            numIdentities = len(set(y + [-1]))
            if numIdentities <= 1:
                return

            param_grid = [
                {'C': [1, 10, 100, 1000],
                 'kernel': ['linear']},
                {'C': [1, 10, 100, 1000],
                 'gamma': [0.001, 0.0001],
                 'kernel': ['rbf']}
            ]
            self.svm = GridSearchCV(SVC(C=1), param_grid, cv=5).fit(X, y)

    def processFrame(self, dataURL, identity, training):
        msg = {}

        head = "data:image/jpeg;base64,"
        assert(dataURL.startswith(head))
        imgdata = base64.b64decode(dataURL[len(head):])
        imgF = StringIO.StringIO()
        imgF.write(imgdata)
        imgF.seek(0)
        img = Image.open(imgF)

        buf = np.fliplr(np.asarray(img))
        rgbFrame = np.zeros((300, 400, 3), dtype=np.uint8)
        rgbFrame[:, :, 0] = buf[:, :, 2]
        rgbFrame[:, :, 1] = buf[:, :, 1]
        rgbFrame[:, :, 2] = buf[:, :, 0]

        if not training:
            annotatedFrame = np.copy(buf)

        # cv2.imshow('frame', rgbFrame)
        # if cv2.waitKey(1) & 0xFF == ord('q'):
        #     return

        identities = []
        # bbs = align.getAllFaceBoundingBoxes(rgbFrame)
        bb = align.getLargestFaceBoundingBox(rgbFrame)
        bbs = [bb] if bb is not None else []
        for bb in bbs:
            # print(len(bbs))
            landmarks = align.findLandmarks(rgbFrame, bb)
            alignedFace = align.align(args[0].imgDim, rgbFrame, bb,
                                      landmarks=landmarks,
                                      landmarkIndices=openface.AlignDlib.OUTER_EYES_AND_NOSE)
            if alignedFace is None:
                continue

            phash = str(imagehash.phash(Image.fromarray(alignedFace)))
            if phash in self.images:
                identity = self.images[phash].identity
            else:
                rep = net.forward(alignedFace)
                # print(rep)
                if training:
                    self.images[phash] = Face(rep, identity)
                    # TODO: Transferring as a string is suboptimal.
                    # content = [str(x) for x in cv2.resize(alignedFace, (0,0),
                    # fx=0.5, fy=0.5).flatten()]
                    content = [str(x) for x in alignedFace.flatten()]
                    msg["NEW_IMAGE"] = {
                        "hash": phash,
                        "content": content,
                        "identity": identity,
                        "representation": rep.tolist()
                    }
                else:
                    if len(self.people) == 0:
                        identity = -1
                    elif len(self.people) == 1:
                        identity = 0
                    elif self.svm:
                        identity = self.svm.predict(rep)[0]
                    else:
                        print("hhh")
                        identity = -1
                    if identity not in identities:
                        identities.append(identity)

            if not self.training:
                bl = (bb.left(), bb.bottom())
                tr = (bb.right(), bb.top())
                cv2.rectangle(annotatedFrame, bl, tr, color=(153, 255, 204),
                              thickness=3)
                for p in openface.AlignDlib.OUTER_EYES_AND_NOSE:
                    cv2.circle(annotatedFrame, center=landmarks[p], radius=3,
                               color=(102, 204, 255), thickness=-1)
                if identity == -1:
                    if len(self.people) == 1:
                        name = self.people[0]
                    else:
                        name = "Unknown"
                else:
                    name = self.people[identity]
                cv2.putText(annotatedFrame, name, (bb.left(), bb.top() - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.75,
                            color=(152, 255, 204), thickness=2)

        if not training:
            msg["IDENTITIES"] = {
                "identities": identities
            }

            plt.figure()
            plt.imshow(annotatedFrame)
            plt.xticks([])
            plt.yticks([])

            imgdata = StringIO.StringIO()
            plt.savefig(imgdata, format='png')
            imgdata.seek(0)
            content = 'data:image/png;base64,' + \
                urllib.quote(base64.b64encode(imgdata.buf))
            msg["ANNOTATED"] = {
                "content": content
            }
            plt.close()
        return msg


def one_time_startup():
    global open_face
    open_face = OpenFaceServerProtocol()
    open_face.loadData()
