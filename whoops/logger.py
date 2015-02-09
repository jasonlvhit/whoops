import logging


class Logger(object):

    def __init__(self):
        FORMAT = '[%(levelname)s] %(asctime)-15s %(message)s'
        logging.basicConfig(format=FORMAT)
        self.d = {}
        self.logger = logging.getLogger('whoops async ioloop')
        self.logger.setLevel(logging.DEBUG)

    def setlevel(self, levelname):
        self.logger.setLevel(levelname)

    def warning(self, s, *args, **kwargs):
        self.logger.warning(s, *args, extra=self.d)

    def info(self, s, *args, **kwargs):
        self.logger.info(s, *args, extra=self.d)

    def debug(self, s, *args, **kwargs):
        self.logger.debug(s, *args, extra=self.d)

    def error(self, s, *args, **kwargs):
        self.logger.error(s, *args, extra=self.d)
