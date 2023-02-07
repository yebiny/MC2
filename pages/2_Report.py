import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
import json
import cv2
import numpy as np
import datetime
import shutil
from scripts.tflite_lib import *
import io
import subprocess

def get_video_info(video_path):
    # so now we can process it with OpenCV functions
    cap = cv2.VideoCapture(video_path)

    # grab some parameters of video to use them for writing a new, processed video
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)  ##<< No need for an int
    n_frames = cap.get(7)
    return cap, w, h, fps, n_frames


def detect_video(model, video_info, save_path):
    cap, w, h, fps, n_frames = video_info 
    # specify a writer to write a processed video to a disk frame by frame
    fourcc_mp4 = cv2.VideoWriter_fourcc(*'mp4v')
    out_mp4 = cv2.VideoWriter(save_path, fourcc_mp4, fps, (w, h))
   
    p = st.progress(0)
    i = 0 
    while True:
        ret, frame = cap.read()
        if not ret: break
        if i%int(fps)==0: #1초마다
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) 
            detections = model.detect(frame)
            frame = visualize(frame, detections)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR) 
        frame = visualize(frame, detections)
        out_mp4.write(frame)
        i+=1
        p.progress(int((i/n_frames)*100))
        
        
 
def main():
    
    # 파이어베이스 db에서 정보 가져오기
    key_dict = json.loads(st.secrets["textkey"])
    creds = service_account.Credentials.from_service_account_info(key_dict)
    db = firestore.Client(credentials=creds)
    collection = db.collection("user001")
    # 모델 불러오기
    model_path = 'models/effdet_v5.tflite'   
    model = load_model(model_path)
    
    
    st.title('리포트')
    select_y, select_m, select_d = 2023, 2, 1
    date_input= st.date_input("분석할 날짜를 선택하세요.", datetime.date(select_y, select_m, select_d) )
    select_y, select_m, select_d = str(date_input).split('-') 

    ds = []
    started = False
    for doc in collection.stream():
        y, m, d, h, mi, se = doc.id.split('_')
        if [select_y, select_m, select_d] != [y, m, d]: 
            if started: break
            else: continue
        started = True
        url = doc.to_dict()["URL"]
        analyzed = doc.to_dict()["Analysis"]
        ds.append([doc.id, h, mi, se, url, analyzed])

    # 해당 날짜 영상이 있으면
    if bool(ds):    
      for (doc_id, h, mi, se, url, analyzed) in ds:
        c1, c2 = st.columns(2)
        with c1:
            if eval(analyzed): st.write(f'- {h}시 {mi}분 {se}초 : 분석 전')
            else: st.write(f'- {h}시 {mi}분 {se}초 : 분석 완료')
        with c2:
            st.button('영상 플레이', key=doc.id)

        
    
    


        #video_info = get_video_info(url)
        #detect_video( model, video_info, save_path)
        #subprocess.call(f"ffmpeg -y -i {save_path} -c:v libx264 {cvt_path}", shell=True)
        #st.video(cvt_path)
    



if __name__ == '__main__':
    main()
