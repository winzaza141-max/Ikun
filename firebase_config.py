import firebase_admin
from firebase_admin import credentials, firestore
import os

# ตรวจสอบพาธคีย์บน Render
if os.path.exists('/etc/secrets/serviceAccountKey.json'):
    cred_path = '/etc/secrets/serviceAccountKey.json'
else:
    cred_path = 'serviceAccountKey.json'

cred = credentials.Certificate(cred_path)

# เริ่มต้น Firebase แบบใช้แค่ Firestore (ไม่ต้องใส่ storageBucket)
firebase_admin.initialize_app(cred)

db = firestore.client()