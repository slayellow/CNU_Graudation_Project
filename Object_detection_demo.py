import os
import cv2
import numpy as np
import tensorflow as tf
import label_map_util
import visualization_utils as vis_util
from calculate_region import CalculateRegion
import time


class ObjectDetection(object):


    def __init__(self, object_path):
        '''
            MODEL_NAME : 모델이름
            PATH_TO_CKPT : 체크포인트 경로
            PATH_TO_LABELS : 라벨 맵 경로
            PATH_TO_OBJECT : 이미지/비디오 경로
            NUM_CLASSES : 클래스 개수
            generate variable and object / run load_setting function
        :param object_path: path of video
        '''
        self.MODEL_NAME = 'inference_graph_160'
        self.PATH_TO_CKPT = os.path.join('./',self.MODEL_NAME,'frozen_inference_graph.pb')
        self.PATH_TO_LABELS = os.path.join('./','training','label_map.pbtxt')
        self.PATH_TO_OBJECT = object_path
        self.NUM_CLASSES = 8
        self.load_setting()
        self.cal = CalculateRegion()

    def load_setting(self):
        '''
         Load all setting
        '''
        label_map = label_map_util.load_labelmap(self.PATH_TO_LABELS) # 라벨맵 경로에 있는 파일을 읽어서 파싱 및 작업을 통해 라벨맵 작업
        categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=self.NUM_CLASSES, use_display_name=True) # 작업한 라벨맵을 카테고리화 하기 위한 변환작업
        self.category_index = label_map_util.create_category_index(categories) # 카테고리 인덱스
        detection_graph = tf.Graph()
        with detection_graph.as_default():
            od_graph_def = tf.GraphDef()
            with tf.gfile.GFile(self.PATH_TO_CKPT, 'rb') as fid:
                serialized_graph = fid.read()
                od_graph_def.ParseFromString(serialized_graph)
                tf.import_graph_def(od_graph_def, name='')
            config = tf.ConfigProto()
            config.gpu_options.per_process_gpu_memory_fraction = 0.8        # GPU 할당량
            self.sess = tf.Session(config=config, graph=detection_graph)
        self.image_tensor = detection_graph.get_tensor_by_name('image_tensor:0')
        self.detection_boxes = detection_graph.get_tensor_by_name('detection_boxes:0')
        self.detection_scores = detection_graph.get_tensor_by_name('detection_scores:0')
        self.detection_classes = detection_graph.get_tensor_by_name('detection_classes:0')
        self.num_detections = detection_graph.get_tensor_by_name('num_detections:0')

    def video_detection(self, lane, output_path, log):
        """
        run object detection
        :param lane: LaneDetection object
        :param input_path: Input path
        :param output_path: Output path
        :param log: logger object
        """
        temp_line = []      # 이전 라인 좌표 저장을 위한 리스트
        start_time = time.time()    # 시작 시간
        # 비디오 가져오기
        cap = cv2.VideoCapture(self.PATH_TO_OBJECT)
        ret, frame = cap.read()
        height, width, _ = frame.shape
        # 결과 비디오 생성
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        output = cv2.VideoWriter(output_path, fourcc, 29.97, (width, height) )

        cnt = 0         # Frame 체크용
        check = False   # 위험상황 감지 확인용

        while True:
            ret, frame = cap.read()
            if ret is True:
                lines = lane.pipeline(frame, temp_line, log)     # 라인 인식하기
                if not lines:
                    lines = temp_line
                else:
                    temp_line = lines

                # 물체 인식 하기
                image_expanded = np.expand_dims(frame, axis=0)
                (boxes, scores, classes, num) = self.sess.run(
                    [self.detection_boxes, self.detection_scores, self.detection_classes, self.num_detections],
                    feed_dict={self.image_tensor: image_expanded})
                _, bounding_box = vis_util.visualize_boxes_and_labels_on_image_array(
                    frame,
                    np.squeeze(boxes),
                    np.squeeze(classes).astype(np.int32),
                    np.squeeze(scores),
                    self.category_index,
                    use_normalized_coordinates=True,
                    line_thickness=8,
                    min_score_thresh=0.80)
                frame = lane.draw_lines(frame, [lines], thickness=5, )      # 라인 그리기

                if lines:
                    frame, check = self.cal.calculate_region_video(frame, bounding_box, lines)
                    # frame : 위험상황 감지후 나오는 이미지 / check : 위험상황 감지하면 True, 아니면 False
                cnt += 1
                output.write(frame)
                if check:
                    log.logger.info('Frame %s : --------------------------- Warning!!!------------------------- ' % (str(cnt)))
                vis_util.reset()
                k = cv2.waitKey(40) & 0xff
                if k == 27:
                    break
            else:
                break
        cv2.destroyAllWindows()
        output.release()
        cap.release()
        log.logger.info('------------- 소요시간 : %s seconds --------------' % (str(time.time() - start_time)))