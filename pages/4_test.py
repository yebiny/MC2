import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
import json

key_dict = json.loads(st.secrets["textkey"])
st.text('key')
creds = service_account.Credentials.from_service_account_info(key_dict)
st.text('creds')
db = firestore.Client(credentials=creds, project="Monchaton2022")
st.text('db')

collection = db.collection('user001')
st.text('collections')

# For a reference to a collection, we use .stream() instead of .get()
for doc in collection.get():
	st.write("The id is: ", doc.id)
	st.write("The contents are: ", doc.to_dict())
  
  
#st.text(collections)
#ref = db.document('Videos')
#st.text('ref')
#st.text(ref)
#for collection in collections:
#    st.text(collections)
#    for doc in collection.stream():
#        st.text(f'{doc.id} => {doc.to_dict()}')


