import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
import json
import cv2

key_dict = json.loads(st.secrets["textkey"])
creds = service_account.Credentials.from_service_account_info(key_dict)
db = firestore.Client(credentials=creds)
collection = db.collection("user001")

st.title('반려캠 ')

for doc in collection.stream():
  post = doc.to_dict()
  video_name = post['File_title']
  url = post['URL']
  
  st.subheader(f"Date: {video_name}")
  cap = cv2.VideoCapture(url)
  ret, frame = cap.read()
  st.image(frame)
