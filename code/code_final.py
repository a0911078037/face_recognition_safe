import snowboydecoder
import sys
import signal
import os

from imutils.video import VideoStream
from imutils.video import FPS
import face_recognition
import imutils
import pickle
import time
import cv2

import RPi.GPIO as GPIO

import requests

ENDPOINT = "things.ubidots.com"
DEVICE_LABEL = "weather-station"
VARIABLE_LABEL = "opened"
TOKEN = "BBFF-gmkkTyqNgfU7RzCfghfCxKk0EcgMli" # replace with your TOKEN
CONTROL_PIN = 17
PWM_FREQ = 50
STEP=15

GPIO.setmode(GPIO.BCM)
GPIO.setup(CONTROL_PIN, GPIO.OUT)
pwm = GPIO.PWM(CONTROL_PIN, PWM_FREQ)
pwm.start(0)

interrupted = False

def post_var(payload, url=ENDPOINT, device=DEVICE_LABEL, token=TOKEN):
    try:
        url = "http://{}/api/v1.6/devices/{}".format(url, device)
        headers = {"X-Auth-Token": token, "Content-Type": "application/json"}

        attempts = 0
        status_code = 400

        while status_code >= 400 and attempts < 5:
            print("[INFO] Sending data, attempt number: {}".format(attempts))
            req = requests.post(url=url, headers=headers,
                                json=payload)
            status_code = req.status_code
            attempts += 1
            time.sleep(1)
            print(req)
        print("[INFO] Results:")
        print(req.text)
    except Exception as e:
        print("[ERROR] Error posting, details: {}".format(e))
def signal_handler(signal, frame):
    global interrupted
    interrupted = True


def interrupt_callback():
    global interrupted
    return interrupted

def angle_to_duty_cycle(angle=0):
    duty_cycle = (0.05 * PWM_FREQ) + (0.19 * PWM_FREQ * angle / 180)
    return duty_cycle
def close():
    dc = angle_to_duty_cycle(180)
    pwm.ChangeDutyCycle(dc)
    time.sleep(2)
def face():
    print("[INFO] loading encodings + face detector...")
    data = pickle.loads(open('encodings.pickle3', "rb").read())
    detector = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

# initialize the video stream and allow the camera sensor to warm up
    print("[INFO] starting video stream...")
# vs = VideoStream(src=0).start()
    vs = VideoStream(src=0).start()
    time.sleep(2.0)

    names = []
    count=0
    flag=False
# start the FPS counter
    fps = FPS().start()

# loop over frames from the video file stream
    while True:
    # grab the frame from the threaded video stream and resize it
    # to 500px (to speedup processing)
        frame = vs.read()
        frame = imutils.resize(frame, width=500)
    # convert the input frame from (1) BGR to grayscale (for face
    # detection) and (2) from BGR to RGB (for face recognition)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    # detect faces in the grayscale frame
    # scaleFactor : 
        rects = detector.detectMultiScale(gray, scaleFactor=1.1, 
            minNeighbors=5, minSize=(30, 30))

    # OpenCV returns bounding box coordinates in (x, y, w, h) order
    # but we need them in (top, right, bottom, left) order, so we
    # need to do a bit of reordering
        boxes = [(y, x + w, y + h, x) for (x, y, w, h) in rects]
    # compute the facial embeddings for each face bounding box
        encodings = face_recognition.face_encodings(rgb, boxes)
        names.clear()

    # loop over the facial embeddings
        for encoding in encodings:
        # attempt to match each face in the input image to our known
        # encodings
            matches = face_recognition.compare_faces(data["encodings"],
                encoding)
            name = "Unknown"
        # check to see if we have found a match
            if True in matches:
            # find the indexes of all matched faces then initialize a
            # dictionary to count the total number of times each face
            # was matched
                matchedIdxs = [i for (i, b) in enumerate(matches) if b]
                counts = {}
            # loop over the matched indexes and maintain a count for
            # each recognized face face
                for i in matchedIdxs:
                    name = data["names"][i]
                    counts[name] = counts.get(name, 0) + 1
            # determine the recognized face with the largest number
            # of votes (note: in the event of an unlikely tie Python
            # will select first entry in the dictionary)
                name = max(counts, key=counts.get)
        
        # update the list of names
            names.append(name)
        # loop over the recognized faces
    # for ((top, right, bottom, left), name) in zip(boxes, names):
    # 	# draw the predicted face name on the image
    # 	cv2.rectangle(frame, (left, top), (right, bottom),
    # 		(0, 255, 0), 2)
    # 	y = top - 15 if top - 15 > 15 else top + 15
    # 	cv2.putText(frame, name, (left, y), cv2.FONT_HERSHEY_SIMPLEX,
    # 		0.75, (0, 255, 0), 2)
    # display the image to our screen
        cv2.imshow("Frame", frame)
        key = cv2.waitKey(1) & 0xFF
    # if the `q` key was pressed, break from the loop
        if key == ord("q"):
            break
    # update the FPS counter
        fps.update()

        namesLength = len(names)
    #count = 0

        for name in names:
            if name == "Unknown":
                count+=1
            else:
                print(name)
                payload={VARIABLE_LABEL:{"value":1,"context":{"name":name}}}
                post_var(payload)
                flag=True
                break

        if count >=1 and namesLength!=0:
            os.system('aplay -Dhw:0,0 unknown.mp3')
            break
        if flag:
            break

# stop the timer and display FPS information
    fps.stop()
# do a bit of cleanup
    cv2.destroyAllWindows()
    vs.stop()
    if flag:
        dc = angle_to_duty_cycle(90)
        pwm.ChangeDutyCycle(dc)
        time.sleep(2)
while True:
    models = ['resources/models/open.pmdl','resources/models/close.pmdl']
    signal.signal(signal.SIGINT, signal_handler)
    sensitivity = [0.5]*len(models)
    detector = snowboydecoder.HotwordDetector(models, sensitivity=sensitivity)
    callbacks = [lambda:face(),
                 lambda:close()]
    os.system('aplay -Dhw:0,0 start.mp3')

# main loop
# make sure you have the same numbers of callbacks and models
    
    try:
        detector.start(detected_callback=callbacks,
                   interrupt_check=interrupt_callback,
                   sleep_time=0.03)    
    except KeyboardInterrupt:
        pwm.stop()
        GPIO.cleanup()
        detector.terminate()
    finally:
        pwm.stop()
        GPIO.cleanup()
        detector.terminate()
