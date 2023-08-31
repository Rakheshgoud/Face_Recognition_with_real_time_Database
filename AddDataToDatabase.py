import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://faceattendancerealtime-4c1b7-default-rtdb.firebaseio.com/"
})

ref = db.reference('Students')

data = {
    "202":
        {
            "name": "Virat",
            "major": "Robotics",
            "starting_year": 2017,
            "total_attendance": 7,
            "standing": "G",
            "year": 4,
            "last_attendance_time": "2022-12-11 00:54:34"
        },
    "203":
            {
                "name": "Dhoni",
                "major": "Economics",
                "starting_year": 2021,
                "total_attendance": 12,
                "standing": "B",
                "year": 1,
                "last_attendance_time": "2022-12-11 00:54:34"
            },
    "201":
        {
            "name": "Elon Musk",
            "major": "Physics",
            "starting_year": 2020,
            "total_attendance": 7,
            "standing": "G",
            "year": 2,
            "last_attendance_time": "2022-12-11 00:54:34"
        },
    "260":
        {
            "name": "Rakhesh",
            "major": "CSE",
            "starting_year": 2020,
            "total_attendance": 1,
            "standing": "G",
            "year": 4,
            "last_attendance_time": "2022-12-11 00:54:34"
        }
}

for key, value in data.items():
    ref.child(key).set(value)