import logging.handlers

class Logger(object):


    def __init__(self):
        """
        generate logging and write info
        """
        self.logger = logging.getLogger('log')
        self.formatter = logging.Formatter('[%(levelname)s|%(filename)s:%(lineno)s] %(asctime)s > %(message)s')
        self.generate_handler()
        self.logger.info('-------------------- Log Start -----------------')

    def generate_handler(self):
        """
        generate handler and set handler
        """
        fileHandler = logging.FileHandler('log.log')
        streamHandler = logging.StreamHandler()
        self.set_handler(fileHandler, streamHandler)
        self.set_logger(fileHandler, streamHandler)

    def set_handler(self, fileHandler, streamHandler):
        """
        set handler
        :param fileHandler: .log file setting
        :param streamHandler: console setting
        """
        fileHandler.setFormatter(self.formatter)
        streamHandler.setFormatter(self.formatter)

    def set_logger(self, fileHandler, streamHandler):
        """
        set logger
        :param fileHandler: .log file handler
        :param streamHandler: console handler
        """
        self.logger.addHandler(fileHandler)
        self.logger.addHandler(streamHandler)
        self.logger.setLevel(logging.DEBUG)
