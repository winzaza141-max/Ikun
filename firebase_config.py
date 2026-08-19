import firebase_admin
from firebase_admin import credentials, firestore
import os
import json

# ตรวจสอบ Credentials
if os.environ.get('FIREBASE_SERVICE_ACCOUNT'):
    # อ่านจาก Vercel Environment Variable
    cred_json = json.loads(os.environ.get('FIREBASE_SERVICE_ACCOUNT'))
    cred = credentials.Certificate(cred_json)
elif os.path.exists('serviceAccountKey.json'):
    # อ่านจากไฟล์ Local เครื่องเรา
    cred = credentials.Certificate('serviceAccountKey.json')
else:
    raise FileNotFoundError("ไม่พบไฟล์หรือค่า Firebase Credentials")

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()