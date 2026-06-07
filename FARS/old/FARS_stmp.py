import os
import pickle
import numpy as np
import cv2
import face_recognition
import firebase_admin
from firebase_admin import credentials, db, storage
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Initialize Firebase
cred = credentials.Certificate("ServiceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://fars-81b18-default-rtdb.firebaseio.com/",
    'storageBucket': "fars-81b18.appspot.com"
})
bucket = storage.bucket()

# Setup video capture
video_capture = cv2.VideoCapture(0)
video_capture.set(3, 640)
video_capture.set(4, 480)
background_image = cv2.imread('Resources/background.png')

# Load mode images
mode_images_folder = 'Resources/Modes'
mode_image_files = os.listdir(mode_images_folder)
mode_images = [cv2.imread(os.path.join(mode_images_folder, file)) for file in mode_image_files]

# Load known face encodings
with open('EncodeFile.p', 'rb') as file:
    known_encodings_with_ids = pickle.load(file)
known_encodings, student_ids = known_encodings_with_ids

print("Encode File Loaded")

current_mode = 0
frame_count = 0
current_id = -1
student_image = []

# List to store attendance updates
attendance_updates = []

# Email Configuration
smtp_server = 'smtp.gmail.com'
smtp_port = 587
sender_email = 'sumarmadhavan@gmail.com'
sender_password = 'svivtdwbyuslgphy'
recipient_email = 'hodsc@sairamit.edu.in'

def send_email(attendance_updates):
    subject = "Student Attendance Log"
    body = ""
    for student_info in attendance_updates:
        body += f"""
        Student ID: {student_info['id']}
        Name: {student_info['name']}
        Department: {student_info['Department']}
        Starting Year: {student_info['starting_year']}
        Total Attendance: {student_info['total_attendance']}
        Standing: {student_info['standing_Rank']}
        Year: {student_info['year']}
        Last Logged Time: {student_info['last_logged_time']}
        \n"""

    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = recipient_email
    message['Subject'] = subject
    message.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, message.as_string())
        print("Email sent successfully")
    except Exception as e:
        print(f"Failed to send email: {e}")

while True:
    ret, frame = video_capture.read()
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

    face_locations = face_recognition.face_locations(rgb_small_frame)
    face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

    background_image[162:162 + 480, 55:55 + 640] = frame
    background_image[44:44 + 633, 808:808 + 414] = mode_images[current_mode]

    if face_locations:
        for face_encoding, face_location in zip(face_encodings, face_locations):
            matches = face_recognition.compare_faces(known_encodings, face_encoding)
            face_distances = face_recognition.face_distance(known_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)

            if matches[best_match_index]:
                top, right, bottom, left = face_location
                top, right, bottom, left = top * 4, right * 4, bottom * 4, left * 4
                bounding_box = (55 + left, 162 + top, right - left, bottom - top)
                cv2.rectangle(background_image, (bounding_box[0], bounding_box[1]), 
                              (bounding_box[0] + bounding_box[2], bounding_box[1] + bounding_box[3]), (255, 0, 0), 2)
                current_id = student_ids[best_match_index]

                if frame_count == 0:
                    cv2.putText(background_image, "Loading", (275, 400), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                    cv2.imshow("FARS", background_image)
                    cv2.waitKey(1)
                    frame_count = 1
                    current_mode = 1

        if frame_count != 0:
            if frame_count == 1:
                student_info = db.reference(f'Students/{current_id}').get()
                student_info['id'] = current_id  # Add student ID to the info
                print(student_info)
                blob = bucket.get_blob(f'Images/{current_id}.png')
                if blob:
                    img_array = np.frombuffer(blob.download_as_string(), np.uint8)
                    student_image = cv2.imdecode(img_array, cv2.COLOR_BGRA2BGR)
                    if student_image.shape[:2] != (216, 216):
                        student_image = cv2.resize(student_image, (216, 216))
                    last_logged_time = datetime.strptime(student_info['last_logged_time'], "%Y-%m-%d %H:%M:%S")
                    elapsed_time = (datetime.now() - last_logged_time).total_seconds()
                    print(elapsed_time)

                    if elapsed_time > 30:
                        ref = db.reference(f'Students/{current_id}')
                        student_info['total_attendance'] += 1
                        ref.child('total_attendance').set(student_info['total_attendance'])
                        ref.child('last_logged_time').set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        # Update student_info with the latest data
                        student_info['last_logged_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        attendance_updates.append(student_info)  # Add to attendance updates list
                    else:
                        current_mode = 3
                        frame_count = 0
                        background_image[44:44 + 633, 808:808 + 414] = mode_images[current_mode]
                else:
                    print(f"Blob not found for ID: {current_id}")

            if current_mode != 3:
                if 10 < frame_count < 20:
                    current_mode = 2

                background_image[44:44 + 633, 808:808 + 414] = mode_images[current_mode]

                if frame_count <= 10:
                    cv2.putText(background_image, str(student_info['Department']), (1006, 550),
                                cv2.FONT_HERSHEY_COMPLEX, 0.5, (0, 0, 0), 1)
                    cv2.putText(background_image, str(current_id), (1006, 493),
                                cv2.FONT_HERSHEY_COMPLEX, 0.5, (0, 0, 0), 1)

                    (text_width, text_height), _ = cv2.getTextSize(student_info['name'], cv2.FONT_HERSHEY_COMPLEX, 1, 1)
                    text_offset = (414 - text_width) // 2
                    cv2.putText(background_image, str(student_info['name']), (808 + text_offset, 445),
                                cv2.FONT_HERSHEY_COMPLEX, 1, (50, 50, 50), 1)

                    background_image[175:175 + 216, 909:909 + 216] = student_image

                frame_count += 1

                if frame_count >= 20:
                    frame_count = 0
                    current_mode = 0
                    student_info = []
                    student_image = []
                    background_image[44:44 + 633, 808:808 + 414] = mode_images[current_mode]

    else:
        current_mode = 0
        frame_count = 0

    cv2.imshow("Face Attendance", background_image)

    # Check for 'q' key press to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Send email with all attendance updates after quitting
if attendance_updates:
    send_email(attendance_updates)

# Release the video capture and close windows
video_capture.release()
cv2.destroyAllWindows()
