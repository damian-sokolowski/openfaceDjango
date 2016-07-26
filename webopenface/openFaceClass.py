from PIL import Image
from sklearn.grid_search import GridSearchCV
from sklearn.svm import SVC
from webopenface.models import Person, DetectedPeople, PeopleFace, Frame, DetectedFace

import argparse
import base64
import cv2
import imagehash
import numpy as np
import openface
import os
import StringIO

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

align = openface.AlignDlib(args[0].dlibFacePredictor)
net = openface.TorchNeuralNet(args[0].networkModel, imgDim=args[0].imgDim,
                              cuda=args[0].cuda)


class Face:

    def __init__(self, rep, identity):
        self.rep = rep
        self.identity = identity

    def __repr__(self):
        return "{{id: {}, rep[0:5]: {}}}".format(
            str(self.identity),
            self.rep[0:5]
        )


class OpenFaceClass:

    def __init__(self):
        self.images = {}
        self.people = []
        self.svm = None
        if args[0].unknown:
            self.unknownImgs = np.load("./examples/web/unknown.npy")

    def __getstate__(self):
        return {'images': self.images, 'people': self.people, 'svm': self.svm}

    def __setstate(self, state):
        self.images, self.people, self.svm = state

    def loadData(self):
        people = Person.objects.all()
        for person in people:
            people_amount = self.addPerson(person.id)
            for dataUrl in person.peopleface_set.all():
                self.processFrame(dataUrl.face, people_amount, True, True)
        self.trainSVM()

    def addPerson(self, id_number):
        self.people.append(id_number)
        return len(self.people) - 1

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

    def processFrame(self, dataURL, identity, training, loadingData=False):
        msg = {}
        detected_people = {}

        head = "data:image/jpeg;base64,"
        assert(dataURL.startswith(head))
        imgdata = base64.b64decode(dataURL[len(head):])
        imgF = StringIO.StringIO()
        imgF.write(imgdata)
        imgF.seek(0)
        img = Image.open(imgF)

        buf = np.fliplr(np.asarray(img))
        rgbFrame = np.zeros((buf.shape[0], buf.shape[1], 3), dtype=np.uint8)
        rgbFrame[:, :, 0] = buf[:, :, 2]
        rgbFrame[:, :, 1] = buf[:, :, 1]
        rgbFrame[:, :, 2] = buf[:, :, 0]

        if not training:
            annotatedFrame = np.copy(buf)

        identities = []
        bbs = align.getAllFaceBoundingBoxes(rgbFrame)
        bbs = bbs if len(bbs) > 0 else []
        # bb = align.getLargestFaceBoundingBox(rgbFrame)
        # bbs = [bb] if bb is not None else []
        for bb in bbs:
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
                img = Image.fromarray(alignedFace, 'RGB')
                imgF = StringIO.StringIO()
                img.save(imgF, format="JPEG")
                imgF.seek(0)
                base_image = head + base64.b64encode(imgF.buf)
                if training:
                    self.images[phash] = Face(rep, identity)
                    if not loadingData:
                        pF = PeopleFace(
                            face=dataURL,
                            person_id=self.people[identity]
                        )
                        pF.save()
                    # TODO: Transferring as a string is suboptimal.
                    # content = [str(x) for x in alignedFace.flatten()]
                    msg["NEW_IMAGE"] = {
                        "hash": phash,
                        "content": base_image,#content,
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
                        detected_people[self.people[identity]] = base_image
                    else:
                        print("hhh")
                        identity = -1
                    if identity not in identities:
                        identities.append(identity)

            if not training:
                bl = (bb.left(), bb.bottom())
                tr = (bb.right(), bb.top())
                cv2.rectangle(annotatedFrame, bl, tr, color=(153, 255, 204),
                              thickness=3)
                for p in openface.AlignDlib.OUTER_EYES_AND_NOSE:
                    cv2.circle(annotatedFrame, center=landmarks[p], radius=3,
                               color=(102, 204, 255), thickness=-1)
                if identity == -1:
                    if len(self.people) == 1:
                        name = Person.objects.get(pk=self.people[0]).name
                    else:
                        name = "Unknown"
                else:
                    name = Person.objects.get(pk=self.people[identity]).name
                cv2.putText(annotatedFrame, name, (bb.left(), bb.top() - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.75,
                            color=(152, 255, 204), thickness=2)
        if not training:
            msg["IDENTITIES"] = {
                "identities": identities
            }

            img = Image.fromarray(annotatedFrame, 'RGB')
            imgF = StringIO.StringIO()
            img.save(imgF, format="JPEG")
            imgF.seek(0)
            content = head + base64.b64encode(imgF.buf)

            msg["ANNOTATED"] = {
                "content": content
            }
            if detected_people:
                fr = Frame(frame=content)
                fr.save()
                for key, value in detected_people.iteritems():
                    df = DetectedFace(frame=fr, face=value)
                    df.save()
                    dp = DetectedPeople(face=df, person_id=key)
                    dp.save()
        return msg