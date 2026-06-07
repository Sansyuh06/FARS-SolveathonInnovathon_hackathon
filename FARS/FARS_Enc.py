"""Encode face images and upload to Firebase Storage (legacy). Run from FARS/."""
from __future__ import annotations

import os
import pickle
import sys

import cv2

FARS_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(FARS_DIR)
sys.path.insert(0, FARS_DIR)

from firebase_setup import init_firebase

try:
    import face_recognition
except ImportError:
    face_recognition = None  # type: ignore
    print("WARNING: face_recognition not installed. Install dlib + face_recognition to encode.")


def resize_img(image, size=(216, 216)):
    return cv2.resize(image, size)


db, bucket = init_firebase(storage=True)

image_folder = "Images"
if not os.path.isdir(image_folder):
    raise FileNotFoundError(f"Missing folder: {image_folder}")

image_files = [f for f in os.listdir(image_folder) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
print(image_files)

images = []
student_ids = []

for file in image_files:
    path = os.path.join(image_folder, file)
    image = cv2.imread(path)
    if image is None:
        print(f"Skipping unreadable image: {file}")
        continue
    resized_image = resize_img(image, (216, 216))
    images.append(resized_image)
    student_ids.append(os.path.splitext(file)[0])
    blob = bucket.blob(f"{image_folder}/{file}")
    blob.upload_from_filename(path)

print(student_ids)


def encode_images(image_list):
    if face_recognition is None:
        raise RuntimeError("face_recognition library required for encoding")
    encodings = []
    for idx, image in enumerate(image_list):
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        face_encodings = face_recognition.face_encodings(rgb_image)
        if face_encodings:
            encodings.append(face_encodings[0])
        else:
            print(f"No face found in image {student_ids[idx]}")
    return encodings


if __name__ == "__main__":
    print("Starting Encoding...")
    known_encodings = encode_images(images)
    encodings_with_ids = [known_encodings, student_ids]
    print("Encoding Finished")

    with open("EncodeFile.p", "wb") as encode_file:
        pickle.dump(encodings_with_ids, encode_file)

    print("File Saved")
