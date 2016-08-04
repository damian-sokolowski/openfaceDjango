from PIL import Image
from sklearn.grid_search import GridSearchCV
from sklearn.svm import SVC
from threading import Lock
from webopenface.models import Person, DetectedPeople, PeopleFace, Frame, DetectedFace

import argparse
import base64
import cv2
import imagehash
import numpy as np
import openface
import operator
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

lock = Lock()


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
        self.fit = []
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
            self.svm = GridSearchCV(SVC(C=1, probability=True), param_grid, cv=5).fit(X, y)

    def findMatching(self, matrix):
        for image_id in dict(matrix):
            users_proba = matrix[image_id]
            user_id = max(users_proba.iteritems(), key=operator.itemgetter(1))[0]
            is_greatest = True
            if users_proba[user_id] < 0.4:
                self.fit.append((image_id, -1, users_proba[user_id]))
                del matrix[image_id]
                continue
            for j in matrix:
                next_users_proba = matrix[j]
                if next_users_proba[user_id] > users_proba[user_id]:
                    is_greatest = False
                    break

            if is_greatest:
                self.fit.append((image_id, user_id, users_proba[user_id]))
                del matrix[image_id]
                for img_id in dict(matrix):
                    del matrix[img_id][user_id]
        if matrix:
            self.findMatching(matrix)

    def processFrame(self, dataURL, identity, training, loadingData=False):
        msg = {}
        detected_faces = {}
        recognized_people = {}
        proba = {}

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
        self.fit = []

        bbs = align.getAllFaceBoundingBoxes(rgbFrame)
        bbs = bbs if len(bbs) > 0 else []
        # bb = align.getLargestFaceBoundingBox(rgbFrame)
        # bbs = [bb] if bb is not None else []
        for key, bb in enumerate(bbs):
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
                lock.acquire()
                try:
                    rep = net.forward(alignedFace)
                finally:
                    lock.release()
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
                    detected_faces[key] = base_image
                    if len(self.people) == 0:
                        self.fit.append((key, -1, 0))
                    elif len(self.people) == 1:
                        self.fit.append((key, 0, 0))
                    elif self.svm:
                        proba[key] = {y: v for ((x, y), v) in np.ndenumerate(self.svm.predict_proba(rep))}
                    else:
                        print("hhh")
                        self.fit.append((key, -1, 0))

        if not training:
            self.findMatching(proba)
            unknown_id =0
            for key, value in enumerate(self.fit):
                image_id = value[0]
                bb = bbs[image_id]
                identity = value[1]

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

                probability = int(value[2]*100)
                identities.append(name+' - '+str(probability)+'%')
                if -1 == identity:
                    recognized_key = 'unknown'+str(unknown_id)
                    unknown_id = unknown_id+1
                else:
                    recognized_key = self.people[identity]
                recognized_people[recognized_key] = detected_faces[image_id]

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
            if recognized_people:
                fr = Frame(frame=content)
                fr.save_delete()
                for key, value in recognized_people.iteritems():
                    person_id = key if isinstance(key, int) else None
                    df = DetectedFace(frame=fr, face=value)
                    df.save()
                    dp = DetectedPeople(face=df, person_id=person_id, probability=probability)
                    dp.save()
        return msg