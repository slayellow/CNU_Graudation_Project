import os
import cv2
import numpy as np
import matplotlib.image as mpimg
import tensorflow as tf
import sys
from lane_detection import Lane
from Lane_Detection_V2 import LaneDetection
# 필요한 유틸리티 임포트
import label_map_util
import visualization_utils as vis_util

# 모델 이름과 이미지 이름
MODEL_NAME = 'inference_graph'
IMAGE_NAME = '000138.png'

# 현재 경로 가져오기
CWD_PATH = os.getcwd()

# 체크포인트 경로
PATH_TO_CKPT = os.path.join(CWD_PATH,MODEL_NAME,'frozen_inference_graph.pb')

# 라벨 맵 경로
PATH_TO_LABELS = os.path.join(CWD_PATH,'training','label_map.pbtxt')

# 테스트할 이미지 경로
PATH_TO_IMAGE = os.path.join(CWD_PATH,'test',IMAGE_NAME)

# 클래스 개수
NUM_CLASSES = 8

# 라벨맵 로드
label_map = label_map_util.load_labelmap(PATH_TO_LABELS) # 라벨맵 경로에 있는 파일을 읽어서 파싱 및 작업을 통해 라벨맵 작업
categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=NUM_CLASSES, use_display_name=True) # 작업한 라벨맵을 카테고리화 하기 위한 변환작업
category_index = label_map_util.create_category_index(categories) # 카테고리 인덱스

# 텐서플로우 이용
detection_graph = tf.Graph()
with detection_graph.as_default():
    od_graph_def = tf.GraphDef()
    with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
        serialized_graph = fid.read()
        od_graph_def.ParseFromString(serialized_graph)
        tf.import_graph_def(od_graph_def, name='')

    sess = tf.Session(graph=detection_graph)

# 물체인식 분류를 위한 인풋과 아웃풋 텐서 작성

# input tensor(이미지) , get_tensor_by_name = placeholder 불러오기
image_tensor = detection_graph.get_tensor_by_name('image_tensor:0')

# Output tensor 는 바운딩박스, 점수(정확도), 클래스(라벨)가 있다.
detection_boxes = detection_graph.get_tensor_by_name('detection_boxes:0')
detection_scores = detection_graph.get_tensor_by_name('detection_scores:0')
detection_classes = detection_graph.get_tensor_by_name('detection_classes:0')

# 클래스(라벨 맵) 숫자
num_detections = detection_graph.get_tensor_by_name('num_detections:0')

# 이미지로 진행 할 때
lane = Lane()
laneV2 = LaneDetection()
image = cv2.imread(PATH_TO_IMAGE)



image_expanded = np.expand_dims(image, axis=0) # 디멘션 확장 하는 함수

# 실제 detection 하는 부분
(boxes, scores, classes, num) = sess.run(
    [detection_boxes, detection_scores, detection_classes, num_detections],
    feed_dict={image_tensor: image_expanded})

# detection 결과 그리기 부분(위에 선언한 vis_util 이용)
vis_util.visualize_boxes_and_labels_on_image_array(
    image,
    np.squeeze(boxes),
    np.squeeze(classes).astype(np.int32),
    np.squeeze(scores),
    category_index,
    use_normalized_coordinates=True,
    line_thickness=8,
    min_score_thresh=0.80)

# Version1 Lane Detection
# image = lane.process_frame(image)

# Version2 Lane Detection

image = laneV2.pipeline(image)
cv2.imwrite('output_000138.jpg',image)
cv2.destroyAllWindows()

'''
# 영상으로 진행할때
cap = cv2.VideoCapture(PATH_TO_IMAGE)
fourcc = cv2.VideoWriter_fourcc(*'XVID')
output = cv2.VideoWriter( 'output.mp4', fourcc, 25.0, (1280,720) )
# 
ret, frame = cap.read()
while(1):
    ret, frame = cap.read()
    print(ret)
    if ret == True:
        image_expanded = np.expand_dims(frame, axis=0) # 디멘션 확장 하는 함수

        # 실제 detection 하는 부분
        (boxes, scores, classes, num) = sess.run(
            [detection_boxes, detection_scores, detection_classes, num_detections],
            feed_dict={image_tensor: image_expanded})

        # detection 결과 그리기 부분(위에 선언한 vis_util 이용)
        vis_util.visualize_boxes_and_labels_on_image_array(
            frame,
            np.squeeze(boxes),
            np.squeeze(classes).astype(np.int32),
            np.squeeze(scores),
            category_index,
            use_normalized_coordinates=True,
            line_thickness=8,
            min_score_thresh=0.80)

        # opencv 이용 이미지 보여주기
        #cv2.imshow('Object detector', frame)
        output.write(frame)
        k = cv2.waitKey(40) & 0xff
        if k == 27:
            break
    # 아무키나 눌렀을때 닫기
    else:
        break
cv2.destroyAllWindows()
output.release()
cap.release()
'''