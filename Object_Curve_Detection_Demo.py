import os
import tensorflow as tf
import label_map_util
import visualization_utils as vis_util
from calculate_curve_region import CalculateCurveRegion
import CurvedLaneDetection
import time
from moviepy.editor import VideoFileClip


class ObjectCurve(object):


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
        self.cal = CalculateCurveRegion()
        self.temp_lines = []
        self.temp_image = []

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

    def process(self, img):
        frame, lines, new_image = CurvedLaneDetection.curve_laneDetection(img, self.temp_image)

        if lines == [] and new_image == []:
            lines = self.temp_line
        else:
            self.temp_line = lines
            self.temp_image = new_image
        # 이부분 주석 해제하면 Object Detection까지 진행
        '''
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

        if lines != []:
            str, frame = self.cal.calculate_region_video(frame, bounding_box, lines)
        '''
        print('Frame : ' + str(lines))

        vis_util.reset()
        return frame

    def video_detection(self, output_name):

        start_time = time.time()
        clip1 = VideoFileClip(self.PATH_TO_OBJECT)
        white_clip = clip1.fl_image(self.process)
        white_clip.write_videofile(output_name, audio=False)
        print('------ 소요시간 : %s seconds ------' % (time.time() - start_time))
