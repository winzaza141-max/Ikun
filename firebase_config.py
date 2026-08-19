import firebase_admin
from firebase_admin import credentials, firestore, storage

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'storageBucket': 'your-project-id.appspot.com'  # เปลี่ยนเป็น Bucket Name ของคุณ
})

db = firestore.client()
bucket = storage.bucket()