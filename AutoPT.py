import time
from threading import Thread

import AutoPT_BYR
import BGIcon
import Myconfig
import Mylogger
import globalvar as gl


def run():
    auto_byr = AutoPT_BYR.Byr()
    while thread_flag:
        auto_byr.start()
        waittime = gl.get_value('config').intervaltime
        while thread_flag and waittime > 0:
            time.sleep(1)
            waittime -= 1


if __name__ == '__main__':
    thread_flag = True

    gl._init()
    gl.set_value('thread', Thread(target=run))
    gl.set_value('config', Myconfig.Config())
    gl.set_value('logger', Mylogger.Mylogger())

    gl.get_value('logger').logger.info('程序启动')
    gl.get_value('thread').start()

    app = BGIcon.MyApp()
    app.MainLoop()

    thread_flag = False
