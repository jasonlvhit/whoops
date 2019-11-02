import logging


class BaseLogger(object):
    def __init__(self):
        self.extra = {}
        self.logger = logging.getLogger("whoops async ioloop")
        self.logger.setLevel(logging.DEBUG)

    def setlevel(self, levelname):
        self.logger.setLevel(levelname)

    def warning(self, s, *args, **kwargs):
        self.logger.warning(s, *args, extra=self.extra)

    def info(self, s, *args, **kwargs):
        self.logger.info(s, *args, extra=self.extra)

    def debug(self, s, *args, **kwargs):
        self.logger.debug(s, *args, extra=self.extra)

    def error(self, s, *args, **kwargs):
        self.logger.error(s, *args, extra=self.extra)


class DefaultLogger(BaseLogger):
    def __init__(self):
        super(DefaultLogger, self).__init__()
        self.FORMAT = "[%(levelname)s] %(asctime)-15s %(message)s"
        ch = logging.StreamHandler()
        formatter = logging.Formatter(self.FORMAT)
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)
