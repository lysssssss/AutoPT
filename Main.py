import time
import traceback
from threading import Thread

import BGIcon
import Myconfig
import Mylogger
import globalvar as gl
from AutoPT_BYR import AutoPT_BYR
from AutoPT_TJU import AutoPT_TJU


def run():
    logger = gl.get_value('logger').logger
    try:
        maxtime = 1
        auto_byr = None
        auto_tju = None


        if gl.get_value('config').switch('byr'):
            auto_byr = AutoPT_BYR()
            maxtime *= gl.get_value('config').intervaltime('byr')

        if gl.get_value('config').switch('tju'):
            auto_tju = AutoPT_TJU()
            maxtime *= gl.get_value('config').intervaltime('tju')
            pass

        counttime = 0

        while thread_flag:
            if auto_byr is not None and counttime % gl.get_value('config').intervaltime('byr') == 0:
                auto_byr.start()
                pass
            if auto_tju is not None and counttime % gl.get_value('config').intervaltime('tju') == 0:
                auto_tju.start()
                pass
            counttime += 1
            if counttime >= maxtime:
                counttime = 0
            time.sleep(1)
    except BaseException:
        logger.exception(traceback.format_exc())
        #traceback.print_exc(file=open('treace.txt', 'w+'))


if __name__ == '__main__':
    thread_flag = True
    gl._init()


    try:
        gl.set_value('config', Myconfig.Config())
        gl.set_value('logger', Mylogger.Mylogger())

        gl.set_value('thread', Thread(target=run))


        app = BGIcon.MyApp()
        gl.set_value('wxpython', app)

        gl.get_value('logger').logger.info('程序启动')
        gl.get_value('thread').start()

        app.MainLoop()
    except BaseException:
        traceback.print_exc(file=open('treace.txt', 'w+'))
        # gl.get_value('logger').logger.exception(traceback.format_exc())
    thread_flag = False
