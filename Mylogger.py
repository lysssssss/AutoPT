from logging import handlers
import logging
import globalvar as gl


class Mylogger(object):

    def __init__(self):
        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '%(asctime)10s [%(filename)s %(levelname)6s:%(lineno)4s - %(funcName)10s ] %(message)s'
        )
        console.setFormatter(formatter)

        self._logger = logging.getLogger("byr")
        self._logger.addHandler(console)
        if gl.get_value('config').loglevel == 'info':
            self._logger.setLevel(logging.INFO)
        else:
            self._logger.setLevel(logging.DEBUG)

        th = handlers.TimedRotatingFileHandler(filename='Run.log', when='midnight',
                                               backupCount=gl.get_value('config').logsavetime,
                                               encoding='utf-8')  # 往文件里写入#指定间隔时间自动生成文件的处理器
        # 实例化TimedRotatingFileHandler
        # interval是时间间隔，backupCount是备份文件的个数，如果超过这个个数，就会自动删除，when是间隔的时间单位，单位有以下几种：
        # S 秒
        # M 分
        # H 小时、
        # D 天、
        # W 每星期（interval==0时代表星期一）
        # midnight 每天凌晨
        th.setFormatter(formatter)  # 设置文件里写入的格式
        self._logger.addHandler(th)

    @property
    def logger(self):
        return self._logger
