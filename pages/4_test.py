import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
import json

key_dict = json.loads(st.secrets["textkey"])
st.text('key')
creds = service_account.Credentials.from_service_account_info(key_dict)
st.text('creds')
db = firestore.Client(credentials=creds, project="Monchaton2022-32941")
st.text('db')
st.text(dir(db))

collections = db.collections()
st.text(collections)
st.text(dir(collections))
for doc in collection.stream():
  st.text(doc.id)

#st.text(collection.steram())

#.document("2023_02_02_20_02_45")
#st.text(doc_ref)


# Then get the data at that reference.
doc = doc_ref.get()


# Let's see what we got!
st.write("The id is: ", doc.id)
st.write("The contents are: ", doc.to_dict())
