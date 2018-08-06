from Object_detection_demo import ObjectDetection
from Lane_Detection_V2 import LaneDetection
import sys

# argv[1] = Input path
# argv[2] = output.path

class Run(object):

    def __init__(self):
        """
        generate LaneDetection object
        """
        self.lane = LaneDetection()

    def run_model(self, log):
        """
        run algorithm
        :param log: logger object
        """
        try:
            log.logger.info('Input File Path : %s' %(sys.argv[1]))
            object_class = ObjectDetection(sys.argv[1])     # generate ObjectDetection object
            object_class.video_detection(self.lane, sys.argv[2], log) # run ObjectDetection function
            log.logger.info('Output File Path : %s' %(sys.argv[2]))
        except FileNotFoundError as e:
            log.logger.error(e)
        finally:
            log.logger.info('-------------------- Log Finish -----------------')
