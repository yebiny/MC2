import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
import json

key_dict = json.loads(st.secrets["textkey"])
st.text('key')
creds = service_account.Credentials.from_service_account_info(key_dict)
st.text('creds')
db = firestore.Client(credentials=creds)
st.text('db')
st.text(dir(db))

collection = db.collection("user001")
st.text(dir(collection))
st.text(collection.stream())
for doc in collection.stream():
  post = doc.to_dict()
  vidoe_name = post['File_title']
  url = post['URL']
  
  st.subheader(f"Date: {vidoe_name}")
	st.write(f":link: [{url}]({url})")
