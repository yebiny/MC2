import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
import json
import cv2
import numpy as np
import cv2

def get_frame_from_url(url):
  cap = cv2.VideoCapture(url)
  loadedImage = None
  while True:
      ret, frame = cap.read()  
      if frame is not None:
        frame = cv2.resize(frame, (300, 200))
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        loadedImage = frame
      break
        
  return loadedImage


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
  
  st.subheader(video_name)
  col1, col2, col3 = st.columns(3)
  with col1:
    st.text("장소:")
  with col2:
    if loadedImage is not None:
      st.image(loadedImage)
  with col3:
    if button('Play'):
      st.write('play!')

    
