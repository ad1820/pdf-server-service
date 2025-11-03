import firebase_admin
from firebase_admin import credentials, auth
from dotenv import load_dotenv
import pyrebase
import os
import json

load_dotenv()

if not firebase_admin._apps:
    cred_dict = json.loads(os.getenv("FIREBASE_CREDENTIALS"))
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)

firebaseConfig = {
    "apiKey": os.getenv("FIREBASE_API_KEY"),
    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
    "projectId": os.getenv("FIREBASE_PROJECT_ID"),
    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
    "appId": os.getenv("FIREBASE_APP_ID"),
    "measurementId": os.getenv("FIREBASE_MEASUREMENT_ID"),
    "databaseURL": ""
}
firebase = pyrebase.initialize_app(firebaseConfig)
pb_auth = firebase.auth()
