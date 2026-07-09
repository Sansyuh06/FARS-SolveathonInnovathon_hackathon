import os
import sys
import pickle
import numpy as np
import cv2
import face_recognition
from datetime import datetime

FARS_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(FARS_DIR)
sys.path.insert(0, FARS_DIR)

from firebase_setup import init_firebase

db, bucket = init_firebase(storage=True)

# Video capture from webcam  
cap = cv2.VideoCapture(1)
cap.set(3, 640)  # Set width
cap.set(4, 480)  # Set height

# Load encoding file
print("Loading Encode File ...")
with open('EncodeFile.p', 'rb') as file:
    encodeListKnownWithIds = pickle.load(file)
encodeListKnown, studentIds = encodeListKnownWithIds
print("Encode File Loaded")

# Initialize variables
frame_skip = 5  # Process every 5th frameq
frame_count = 0

while True:
    success, img = cap.read()
    frame_count += 1

    # Skip frames to speed up processing
    if frame_count % frame_skip != 0:
        continue

    imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

    faceCurFrame = face_recognition.face_locations(imgS)
    encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)

    if faceCurFrame:
        for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
            matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
            faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
            matchIndex = np.argmin(faceDis)

            if matches[matchIndex]:
                id = studentIds[matchIndex]
                studentInfo = db.reference(f'Students/{id}').get()
                blob = bucket.get_blob(f'Images/{id}.png')

                if blob is not None:
                    array = np.frombuffer(blob.download_as_string(), np.uint8)
                    imgStudent = cv2.imdecode(array, cv2.COLOR_BGRA2BGR)

                    datetimeObject = datetime.strptime(studentInfo['last_logged_time'], "%Y-%m-%d %H:%M:%S")
                    secondsElapsed = (datetime.now() - datetimeObject).total_seconds()

                    if secondsElapsed > 30:
                        ref = db.reference(f'Students/{id}')
                        studentInfo['total_attendance'] += 1
                        ref.update({
                            'total_attendance': studentInfo['total_attendance'],
                            'last_logged_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })

                        print(f"Detected... Logged for {studentInfo['name']}")
                else:
                    print(f"Blob not found for ID: {id}")

    key = cv2.waitKey(1)
    if key == 27:  # Press Esc to exit
        break

# Release video capture and close all windows
cap.release()
cv2.destroyAllWindows()
