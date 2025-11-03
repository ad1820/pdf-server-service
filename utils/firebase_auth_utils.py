import base64, os, json, firebase_admin
from firebase_admin import credentials, auth
import pyrebase

# --- Initialize Firebase Admin ---
if not firebase_admin._apps:
    encoded = os.getenv("FIREBASE_CREDENTIALS_B64")

    if encoded:
        try:
            decoded = base64.b64decode(encoded).decode("utf-8")
            cred_dict = json.loads(decoded)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            print("✅ Firebase initialized using FIREBASE_CREDENTIALS_B64 (Render/Prod)")
        except Exception as e:
            print("⚠️ Failed to initialize Firebase from FIREBASE_CREDENTIALS_B64:", e)
    elif os.path.exists("firebase-credentials.json"):
        cred = credentials.Certificate("firebase-credentials.json")
        firebase_admin.initialize_app(cred)
        print("✅ Firebase initialized using local firebase-credentials.json (Dev)")
    else:
        raise ValueError("❌ Firebase credentials not found in env or local file")

# --- Pyrebase Client Config (for Auth) ---
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
