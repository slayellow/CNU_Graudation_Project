class InputDataFields(object):

  image = 'image'
  original_image = 'original_image'
  key = 'key'
  source_id = 'source_id'
  filename = 'filename'
  groundtruth_image_classes = 'groundtruth_image_classes'
  groundtruth_boxes = 'groundtruth_boxes'
  groundtruth_classes = 'groundtruth_classes'
  groundtruth_label_types = 'groundtruth_label_types'
  groundtruth_is_crowd = 'groundtruth_is_crowd'
  groundtruth_area = 'groundtruth_area'
  groundtruth_difficult = 'groundtruth_difficult'
  groundtruth_group_of = 'groundtruth_group_of'
  proposal_boxes = 'proposal_boxes'
  proposal_objectness = 'proposal_objectness'
  groundtruth_instance_masks = 'groundtruth_instance_masks'
  groundtruth_instance_boundaries = 'groundtruth_instance_boundaries'
  groundtruth_instance_classes = 'groundtruth_instance_classes'
  groundtruth_keypoints = 'groundtruth_keypoints'
  groundtruth_keypoint_visibilities = 'groundtruth_keypoint_visibilities'
  groundtruth_label_scores = 'groundtruth_label_scores'
  groundtruth_weights = 'groundtruth_weights'
  num_groundtruth_boxes = 'num_groundtruth_boxes'
  true_image_shape = 'true_image_shape'
  verified_labels = 'verified_labels'
  multiclass_scores = 'multiclass_scores'


class DetectionResultFields(object):

  source_id = 'source_id'
  key = 'key'
  detection_boxes = 'detection_boxes'
  detection_scores = 'detection_scores'
  detection_classes = 'detection_classes'
  detection_masks = 'detection_masks'
  detection_boundaries = 'detection_boundaries'
  detection_keypoints = 'detection_keypoints'
  num_detections = 'num_detections'


class BoxListFields(object):

  boxes = 'boxes'
  classes = 'classes'
  scores = 'scores'
  weights = 'weights'
  objectness = 'objectness'
  masks = 'masks'
  boundaries = 'boundaries'
  keypoints = 'keypoints'
  keypoint_heatmaps = 'keypoint_heatmaps'


