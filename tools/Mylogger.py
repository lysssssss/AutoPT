import logging
from logging import handlers

import tools.globalvar as gl


class LogginRedirectHandler(logging.Handler):
    def __init__(self, ):
        # run the regular Handler __init__
        logging.Handler.__init__(self)

    def emit(self, record):
        msg = self.format(record)
        gl.get_value('logwindow').frame.textctrl.AppendText(msg + '\n')


class Mylogger(object):

    def __init__(self):
        formatter = logging.Formatter(
            '%(asctime)10s [%(filename)s %(levelname)s:%(lineno)s-%(funcName)s]%(message)s')

        self._logger = logging.getLogger("AutoPT")

        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        console.setFormatter(formatter)

        th = handlers.TimedRotatingFileHandler(filename='log/Run.log', when='midnight',
                                               backupCount=gl.get_value('config').logsavetime,
                                               encoding='utf-8')  # 往文件里写入#指定间隔时间自动生成文件的处理器
        th.setLevel(logging.DEBUG)
        # 实例化TimedRotatingFileHandler
        # interval是时间间隔，backupCount是备份文件的个数，如果超过这个个数，就会自动删除，when是间隔的时间单位，单位有以下几种：
        # S 秒
        # M 分
        # H 小时、
        # D 天、
        # W 每星期（interval==0时代表星期一）
        # midnight 每天凌晨
        th.setFormatter(formatter)  # 设置文件里写入的格式

        self.loggingRedirectHandler = LogginRedirectHandler()
        self.loggingRedirectHandler.setFormatter(formatter)
        if gl.get_value('config').loglevel == 'info':
            self.loggingRedirectHandler.setLevel(logging.INFO)
        else:
            self.loggingRedirectHandler.setLevel(logging.DEBUG)

        self._logger.addHandler(th)
        self._logger.addHandler(console)
        self._logger.addHandler(self.loggingRedirectHandler)
        self._logger.setLevel(logging.DEBUG)

    @property
    def logger(self):
        return self._logger
