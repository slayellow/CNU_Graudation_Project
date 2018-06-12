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
        :param object_path: path of image or video
        '''
        self.MODEL_NAME = 'inference_graph'
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
            config.gpu_options.per_process_gpu_memory_fraction = 0.8
            self.sess = tf.Session(config=config, graph=detection_graph)
        self.image_tensor = detection_graph.get_tensor_by_name('image_tensor:0')
        self.detection_boxes = detection_graph.get_tensor_by_name('detection_boxes:0')
        self.detection_scores = detection_graph.get_tensor_by_name('detection_scores:0')
        self.detection_classes = detection_graph.get_tensor_by_name('detection_classes:0')
        self.num_detections = detection_graph.get_tensor_by_name('num_detections:0')

    def image_detection(self, lane, output_name):
        temp_line = []
        start_time = time.time()
        image = cv2.imread(self.PATH_TO_OBJECT)
        image, lines = lane.pipeline(image, temp_line)
        image_expanded = np.expand_dims(image, axis=0)
        (boxes, scores, classes, num) = self.sess.run(
            [self.detection_boxes, self.detection_scores, self.detection_classes, self.num_detections],
            feed_dict={self.image_tensor: image_expanded})
        _, bounding_box = vis_util.visualize_boxes_and_labels_on_image_array(
            image,
            np.squeeze(boxes),
            np.squeeze(classes).astype(np.int32),
            np.squeeze(scores),
            self.category_index,
            use_normalized_coordinates=True,
            line_thickness=8,
            min_score_thresh=0.80)
        print(bounding_box)         # bounding_box 개수만큼 좌표값 출력
        print(lines)                # 2개의 좌표값 출력 ( 영상과는 다르게 라인을 못따면 이미지에선 안보임)
        if lines != []:
            image = self.cal.calculate_region(image, bounding_box, lines)
        cv2.imwrite(output_name+'.jpg',image)
        cv2.destroyAllWindows()
        print('------소요시간 : %s seconds ------'%(time.time() - start_time))

    def video_detection(self, lane, output_name):
        temp_line = []
        start_time = time.time()
        cap = cv2.VideoCapture(self.PATH_TO_OBJECT)
        ret, frame = cap.read()
        height, width, _ = frame.shape

        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        output = cv2.VideoWriter(output_name+'.avi', fourcc, 29.97, (width, height) )

        cnt = 0
        while(1):
            ret, frame = cap.read()
            if ret == True:
                frame, lines = lane.pipeline(frame, temp_line)
                if lines == []:
                    lines = temp_line
                else:
                    temp_line = lines
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

                print('Frame ' + str(cnt+1) + ' Line : ' + str(lines))

                if lines != []:
                    frame = self.cal.calculate_region(frame, bounding_box, lines)
                cnt += 1
                output.write(frame)
                k = cv2.waitKey(40) & 0xff
                if k == 27:
                    break
            else:
                break
        cv2.destroyAllWindows()
        output.release()
        cap.release()
        print('------ 소요시간 : %s seconds ------' % (time.time() - start_time))