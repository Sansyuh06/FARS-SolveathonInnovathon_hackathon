"""Upload student records to Firebase (legacy). Run from the FARS directory."""
from __future__ import annotations

import os
import sys

FARS_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(FARS_DIR)
sys.path.insert(0, FARS_DIR)

from firebase_setup import init_firebase

db, _ = init_firebase(storage=False)
students_ref = db.reference("Students")

students_data = {
    "SIT23SC003": {
        "name": "Shivani M S",
        "Department": "Cyber Security",
        "starting_year": 2023,
        "total_attendance": 0,
        "standing_Rank": "A",
        "year": 2,
        "last_logged_time": "2024-07-07 00:24:34",
    },
    "SIT23SC011": {
        "name": "Rohith Vijay R",
        "Department": "Cyber Security",
        "starting_year": 2023,
        "total_attendance": 0,
        "standing_Rank": "B",
        "year": 2,
        "last_logged_time": "2024-07-07 00:24:34",
    },
    "SIT23SC014": {
        "name": "Akash Santhu Sundar",
        "Department": "Cyber Security",
        "starting_year": 2023,
        "total_attendance": 0,
        "standing_Rank": "B",
        "year": 2,
        "last_logged_time": "2024-07-05 00:54:34",
    },
    "SIT23SC007": {
        "name": "Sumit Madhavan S",
        "Department": "Cyber Security",
        "starting_year": 2023,
        "total_attendance": 0,
        "standing_Rank": "B",
        "year": 2,
        "last_logged_time": "2024-07-05 00:54:34",
    },
    "SIT23SC009": {
        "name": "Harish Sanjay S",
        "Department": "Cyber Security",
        "starting_year": 2023,
        "total_attendance": 0,
        "standing_Rank": "B",
        "year": 2,
        "last_logged_time": "2024-07-05 00:54:34",
    },
    "SIT23SC021": {
        "name": "Cletus Albin",
        "Department": "Cyber Security",
        "starting_year": 2023,
        "total_attendance": 0,
        "standing_Rank": "B",
        "year": 2,
        "last_logged_time": "2024-07-05 00:54:34",
    },
}

if __name__ == "__main__":
    for student_id, student_info in students_data.items():
        students_ref.child(student_id).set(student_info)
    print("Student data uploaded successfully.")
