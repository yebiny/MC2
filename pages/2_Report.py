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
    
    
    # 날짜 선택
    st.title('리포트')
    select_y, select_m, select_d = 2023, 2, 1
    date_input= st.date_input("분석할 날짜를 선택하세요.", datetime.date(select_y, select_m, select_d) )
    select_y, select_m, select_d = str(date_input).split('-') 

    ds = []
    target_url = None
    save_path = None
    started = False
    
    # 선택한 날짜에 해당하는 doc 가져오기
    doc_list = []
    for doc in collection.stream():
        if [select_y, select_m, select_d] != doc.id.split('_')[:3]: 
            if started: break
            else: continue
        started = True
        doc_list.append(doc)

    
    # 해당 날짜 doc에 정보가 있으면
    ## 1. 목록을 나열한다.
    ## 2. 분석하기 버튼을 누르면 분석 시작
    ## 3. 분석 완료된 영상은 플레이 버튼 생성   
    
    if bool(doc_list):
      analyze_button = st.button("분석하기")
      for doc in doc_list:
        doc_id = doc.id
        h, mi, se = doc.id.split('_')[-3:]
        url = doc.to_dict()["URL"]
        analyzed = doc.to_dict()["Analysis"]
        
        c1, c2, c3 = st.columns(3)
        with c1:
            if eval(analyzed): st.write(f'- {h}시 {mi}분 {se}초 : 분석 완료')
            else: st.write(f'- {h}시 {mi}분 {se}초 : 분석 전')
        with c2:
            if st.button('영상 플레이', key=doc_id):
                target_url = url
                save_path = f'./tmp-videos/{doc_id}.mp4'
    
    
    
    if save_path is not None:
        cvt_path = save_path.replace('.mp4', '-cvt.mp4')
        #video_info = get_video_info(target_url)
        #detect_video( model, video_info, save_path)
        #subprocess.call(f"ffmpeg -y -i {save_path} -c:v libx264 {cvt_path}", shell=True)
        st.video(cvt_path)
    



if __name__ == '__main__':
    main()
