import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
import json
import cv2
import numpy as np
import cv2

def get_frame_from_url(url):
  cap = cv2.VideoCapture(url)
  while(cap.isOpened()):
      ret, image = cap.read()    
      loadedImage = cv2.imdecode(image, cv2.IMREAD_COLOR)
      if cv2.waitKey(1) & 0xFF == ord('q'):
          break
      break
  return loadedImage

cap.release()
cv2.destroyAllWindows()
key_dict = json.loads(st.secrets["textkey"])
creds = service_account.Credentials.from_service_account_info(key_dict)
db = firestore.Client(credentials=creds)
collection = db.collection("user001")

st.title('반려캠 ')

for doc in collection.stream():
  post = doc.to_dict()
  video_name = post['File_title']
  url = post['URL']
  loadedImage = get_frame_from_url(url)
  st.text(loadedImage)
