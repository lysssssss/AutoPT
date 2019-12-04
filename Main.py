import time
from threading import Thread

import AutoPT_BYR
import BGIcon
import Myconfig
import Mylogger
import globalvar as gl


def run():
    maxtime = 1
    auto_byr = None
    auto_tju = None

    if gl.get_value('config').switch('byr'):
        auto_byr = AutoPT_BYR.Byr()
        maxtime *= gl.get_value('config').intervaltime('byr')

    if gl.get_value('config').switch('tju'):
        # auto_tju = AutoPT_TJU.Tju()
        maxtime *= gl.get_value('config').intervaltime('tju')
        pass

    counttime = 0

    while thread_flag:
        if auto_byr is not None and counttime % gl.get_value('config').intervaltime('byr') == 0:
            auto_byr.start()
        if auto_tju is not None and counttime % gl.get_value('config').intervaltime('tju') == 0:
            auto_tju.start()
        counttime += 1
        if counttime >= maxtime:
            counttime = 0
        time.sleep(1)


if __name__ == '__main__':
    thread_flag = True

    gl._init()
    gl.set_value('thread', Thread(target=run))
    gl.set_value('config', Myconfig.Config())
    gl.set_value('logger', Mylogger.Mylogger())

    app = BGIcon.MyApp()
    gl.set_value('wxpython', app)

    gl.get_value('logger').logger.info('程序启动')
    gl.get_value('thread').start()

    app.MainLoop()

    thread_flag = False
