import os
import time
import traceback
from threading import Thread

import psutil

import BGIcon
import Myconfig
import Mylogger
import globalvar as gl
from AutoPT_BYR import AutoPT_BYR
from AutoPT_MTEAM import AutoPT_MTEAM
from AutoPT_PTER import AutoPT_PTER
from AutoPT_TJU import AutoPT_TJU


def run():
    logger = gl.get_value('logger').logger
    try:
        maxtime = 1
        auto_byr = None
        auto_tju = None
        auto_pter = None
        auto_mteam = None
        Runqbittorrent()

        if gl.get_value('config').switch('byr'):
            auto_byr = AutoPT_BYR()
            maxtime *= gl.get_value('config').intervaltime('byr')

        if gl.get_value('config').switch('tju'):
            auto_tju = AutoPT_TJU()
            maxtime *= gl.get_value('config').intervaltime('tju')
            pass
        if gl.get_value('config').switch('pter'):
            auto_pter = AutoPT_PTER()
            maxtime *= gl.get_value('config').intervaltime('pter')
            pass
        if gl.get_value('config').switch('mteam'):
            auto_mteam = AutoPT_MTEAM()
            maxtime *= gl.get_value('config').intervaltime('mteam')
            pass
        counttime = 0

        while thread_flag:
            if auto_mteam is not None and counttime % gl.get_value('config').intervaltime('mteam') == 0:
                auto_mteam.start()
                pass
            if auto_tju is not None and counttime % gl.get_value('config').intervaltime('tju') == 0:
                auto_tju.start()
                pass
            if auto_pter is not None and counttime % gl.get_value('config').intervaltime('pter') == 0:
                auto_pter.start()
                pass
            if auto_byr is not None and counttime % gl.get_value('config').intervaltime('byr') == 0:
                auto_byr.start()
                pass

            counttime += 1
            if counttime >= maxtime:
                counttime = 0
            time.sleep(1)
    except BaseException:
        logger.exception(traceback.format_exc())
        # traceback.print_exc(file=open('treace.txt', 'w+'))


def CheckProgramStatus(name):
    list = psutil.pids()
    for i in range(0, len(list)):
        try:
            p = psutil.Process(list[i])
            if 'qbittorrent.exe' in p.name():
                return True
        except BaseException as e:
            # 当某些进程不存在了会有异常，无视即可
            pass
    return False


def Runqbittorrent():
    logger = gl.get_value('logger').logger
    if gl.get_value('config').qbtpath != '':
        try:
            if not CheckProgramStatus('qbittorrent.exe'):
                logger.debug('未检测到QBitTorrent打开，正在尝试打开')
                os.startfile(gl.get_value('config').qbtpath)
                trytime = 60
                while trytime > 0 and (not CheckProgramStatus('qbittorrent.exe')):
                    trytime -= 5
                    logger.info('正在等待QBT启动')
                    time.sleep(5)
                if trytime <= 0:
                    logger.error('QBT启动失败,异常退出')
                else:
                    logger.error('QBT启动成功')
            else:
                logger.debug('QBitTorrent已在运行')
        except BaseException as e:
            logger.exception(traceback.format_exc())


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
