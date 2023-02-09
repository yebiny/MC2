import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
import json
import cv2
import numpy as np
import datetime as dt
import pytz
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

    i=0
    states = []
    while True:
        ret, frame = cap.read()
        if not ret: break
        if i%int(fps)==0: #0.5초마다
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) 
            detections = model.detect(frame)
            for detection in detections:
                states.append( list(list(detection)[1][0])[0] )
            frame = visualize(frame, detections)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR) 
        frame = visualize(frame, detections)
        out_mp4.write(frame)
        i+=1
    return states.count('Vomit')/len(states)
    
def analysis_process(doc, collection, model):	
    
    save_path = f'./tmp-videos/{doc.id}.mp4'
    cvt_path = save_path.replace('.mp4', '-cvt.mp4')
    
    video_info = get_video_info(doc.to_dict()["URL"])
    detect_result = detect_video( model, video_info, save_path)
    
    subprocess.call(f"ffmpeg -y -i {save_path} -c:v libx264 {cvt_path}", shell=True)
    collection.document(f'{doc.id}').set({
        "Analysis": "True",
        "URL": doc.to_dict()['URL']
    })      
    
    return detect_result



    
def main():
    
    # 파이어베이스 db에서 정보 가져오기
    key_dict = json.loads(st.secrets["textkey"])
    creds = service_account.Credentials.from_service_account_info(key_dict)
    db = firestore.Client(credentials=creds)
    collection = db.collection("user001")
    
    # 모델 불러오기
    model_path = 'models/effdet_v5.tflite'   
    model = load_model(model_path)
    
    # 변수 
    ds = []
    save_path = None
    started = False
    target_video = None
    colors = {"분석 전": "Black", "정상": "Green", "구토": "Red"}
    
    # 날짜 선택
    st.title('리포트')
    KST = pytz.timezone('Asia/Seoul')
    now = dt.datetime.now(KST)
    select_y, select_m, select_d = [int(x) for x in str(now).split(' ')[0].split('-') ]
    date_input= st.date_input("분석할 날짜를 선택하세요.", dt.date(select_y, select_m, select_d) )
    select_y, select_m, select_d = str(date_input).split('-') 
    
    # 선택한 날짜에 해당하는 doc 가져오기
    doc_list = []
    for doc in collection.stream():
        if [select_y, select_m, select_d] != doc.id.split('_')[:3]: 
            if started: break
            else: continue
        started = True
        doc_list.append(doc)
    
    # UI: 날짜, 분석 버튼, 프로세스 바
    st.subheader(f'{select_y}년 {select_m}월 {select_d}일')
    c_but, c_p = st.columns(2)
    with c_but: analyze_button = st.button("분석하기")            
    with c_p: p = st.progress(0)
        
    # 비디오 목록생성    
    if bool(doc_list) or analyze_button:
        c1, c2, c3 = st.columns(3)  
        
        # 열 1, 2 : 시간, 플레이 버튼 
        for doc in doc_list:
            doc_id = doc.id
            h, mi, se = doc.id.split('_')[-3:]
            with c1:
                txt = f'<p style="font-family:sans-serif; font-size: 22.5px;">{h}시 {mi}분 {se}초</p>'
                st.markdown(txt, unsafe_allow_html=True)
            with c2:
                play_button =  st.button('Play', key=doc_id)
                if play_button: target_video = f'./tmp-videos/{doc_id}.mp4'.replace('.mp4', '-cvt.mp4')
        
        
        # 열 3: 기존 결과 표시 (기본)
        if not analyze_button:
            for i, doc in enumerate(doc_list):
                # 분석 여부 확인
                analyzed = doc.to_dict()["Analysis"]
                if eval(analyzed):
                    state = doc.to_dict()["Result"]
                else:
                    state = "분석 전"

                with c3:
                    c = colors[state]
                    txt = f'<p style="font-family:sans-serif; color: {c}; font-size: 22.5px;">{state}</p>'
                    st.markdown(txt, unsafe_allow_html=True)
       
                           
        # 만약 분석 버튼 누르면
        else: 
            for i, doc in enumerate(doc_list):
                if not eval(doc.to_dict()["Analysis"]):
                    # 영상 분석 및 저장
                    save_path = f'./tmp-videos/{doc.id}.mp4'
                    video_info = get_video_info(doc.to_dict()["URL"])
                    detect_result = detect_video( model, video_info, save_path)

                    # 분석한 영상 변환
                    cvt_path = save_path.replace('.mp4', '-cvt.mp4')
                    subprocess.call(f"ffmpeg -y -i {save_path} -c:v libx264 {cvt_path}", shell=True)

                    # 결과 파이어베이스 저장
                    if detect_result > 0.5:
                        result = '구토'
                        color = 'Red'
                    else: 
                        result = '정상'
                        color = 'Green'
                    collection.document(f'{doc.id}').set({
                        "Analysis": "True",
                        "URL": doc.to_dict()['URL'],
                        "Result": result,
                        "Confidence": detect_result
                    })     

                    # 목록에 결과 표시
                    with c3:
                        txt = f'<p style="font-family:sans-serif; color:{color}; font-size: 22.5px;">{result}</p>'
                        st.markdown(txt, unsafe_allow_html=True)
                
                else:
                    state = doc.to_dict()["Result"]
                    with c3:
                        c = colors[state]
                        txt = f'<p style="font-family:sans-serif; color: {c}; font-size: 22.5px;">{state}</p>'
                        st.markdown(txt, unsafe_allow_html=True)
                
                p.progress(int(((i+1)/len(doc_list))*100)) # 프로그래스 바 증가
            

                
                

        if target_video is not None:               
            st.video(target_video)
    
if __name__ == '__main__':
    main()
