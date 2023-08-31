import os
import pickle
import cv2
import face_recognition
import cvzone
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage
import numpy as np
from datetime import datetime

# Initialize Firebase credentials
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://faceattendancerealtime-4c1b7-default-rtdb.firebaseio.com/",
    'storageBucket': "faceattendancerealtime-4c1b7.appspot.com"
})
bucket = storage.bucket()

# Initialize webcam capture
cap = cv2.VideoCapture(0)  # Use 0 for the default webcam
cap.set(3, 640)
cap.set(4, 480)

# Load the background image
imgBackground = cv2.imread('Resources/background.png')

# Importing the mode images into a list
folderModePath = 'Resources/Modes'
modePathList = os.listdir(folderModePath)
imgModeList = []
for path in modePathList:
    imgModeList.append(cv2.imread(os.path.join(folderModePath, path)))

# Load the encoding file
print("Loading Encode File ...")
file = open('EncodeFile.p', 'rb')
encodeListKnownWithIds = pickle.load(file)
file.close()
encodeListKnown, studentIds = encodeListKnownWithIds
print("Encode File Loaded")

# Initialize variables
modeType = 0
counter = 0
id = -1
imgStudent = []
face_not_matched_counter = 0  # Counter for tracking face not matched duration
face_match_threshold = 20  # Number of frames (approximately 1 second per frame)

# Main loop
while True:
    # Capture a frame from the webcam
    success, img = cap.read()
    imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (640, 480))

    # Define the region to overlay in the background
    start_height = 162
    end_height = 162 + 480
    start_width = 55
    end_width = 55 + 640
    imgBackground[start_height:end_height, start_width:end_width] = img

    # Face recognition
    faceCurFrame = face_recognition.face_locations(imgS)
    encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)
    if faceCurFrame:
        # Reset the face not matched counter since a face is detected
        face_not_matched_counter = 0

        for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
            matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
            faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
            matchIndex = np.argmin(faceDis)

            if matches[matchIndex]:
                y1, x2, y2, x1 = faceLoc
                y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                bbox = 55 + x1, 162 + y1, x2 - x1, y2 - y1
                imgBackground = cvzone.cornerRect(imgBackground, bbox, rt=0)
                id = studentIds[matchIndex]
                if counter == 0:
                    cvzone.putTextRect(imgBackground, "Loading", (275, 400))
                    cv2.imshow("Face Attendance", imgBackground)
                    cv2.waitKey(1)
                    counter = 1
                    modeType = 1

        if counter != 0:
            if counter == 1:
                # Get student data
                studentInfo = db.reference(f'Students/{id}').get()
                print(studentInfo)
                # Get student image from storage
                blob = bucket.get_blob(f'Images/{id}.png')
                array = np.frombuffer(blob.download_as_string(), np.uint8)
                imgStudent = cv2.imdecode(array, cv2.COLOR_BGRA2BGR)
                # Calculate elapsed time since last attendance
                datetimeObject = datetime.strptime(studentInfo['last_attendance_time'], "%Y-%m-%d %H:%M:%S")
                secondsElapsed = (datetime.now() - datetimeObject).total_seconds()
                print(secondsElapsed)
                if secondsElapsed > 86400:  # 24 hours in seconds
                    # Update attendance data
                    ref = db.reference(f'Students/{id}')
                    studentInfo['total_attendance'] += 1
                    ref.child('total_attendance').set(studentInfo['total_attendance'])
                    ref.child('last_attendance_time').set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                else:
                    modeType = 3
                    counter = 0
                    resized_mode_image = cv2.resize(imgModeList[modeType], (414, 633))
                    imgBackground[44:44 + 633, 808:808 + 414] = resized_mode_image

            if modeType != 3:
                if 10 < counter < 20:
                    modeType = 2

                resized_mode_image = cv2.resize(imgModeList[modeType], (414, 633))
                imgBackground[44:44 + 633, 808:808 + 414] = resized_mode_image

                if counter <= 10:
                    cv2.putText(imgBackground, str(studentInfo['total_attendance']), (861, 125),
                                cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 1)
                    # Other text overlays...

                    imgBackground[175:175 + 216, 909:909 + 216] = imgStudent

                counter += 1

                if counter >= 20:
                    counter = 0
                    modeType = 0
                    studentInfo = []
                    imgStudent = []

    else:
        modeType = 0
        counter = 0
        # Increment the face not matched counter
        face_not_matched_counter += 1

        if face_not_matched_counter >= face_match_threshold:
            # Display "Does Not Match" image
            resized_mode_image = cv2.resize(imgModeList[3], (414, 633))
            imgBackground[44:44 + 633, 808:808 + 414] = resized_mode_image
            print("Does not match")
            # Exit the loop and release resources
            break

    # Display the webcam and overlay images
    cv2.imshow("Face Attendance", imgBackground)

    # Check for user input to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the webcam and close windows
cap.release()
cv2.destroyAllWindows()
