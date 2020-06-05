import os
import time
import traceback
from threading import Thread

import psutil

from autopt.AutoPT_BYR import AutoPT_BYR
from autopt.AutoPT_FRDS import AutoPT_FRDS
from autopt.AutoPT_MTEAM import AutoPT_MTEAM
from autopt.AutoPT_PTER import AutoPT_PTER
from autopt.AutoPT_PTHOME import AutoPT_PTHOME
from autopt.AutoPT_TJU import AutoPT_TJU
from autopt.AutoPT_TTG import AutoPT_TTG
from autopt.QBmanage_Reseed import Manager
from tools import Myconfig, Mylogger, BGIcon
from tools import globalvar as gl
from tools.iyuu import iyuu


def run():
    logger = gl.get_value('logger').logger
    try:
        maxtime = 1
        auto_byr = None
        auto_tju = None
        auto_pter = None
        auto_mteam = None
        auto_pthome = None
        auto_frds = None
        auto_ttg = None

        Runqbittorrent()

        refconfig = {
            'name': 'reseed',
            'ref': {
                'byr': auto_byr,
                'tju': auto_tju,
                'mteam': auto_mteam,
                'pter': auto_pter,
                'pthome': auto_pthome,
                'frds': auto_frds,
                'ttg': auto_ttg
            }
        }
        gl.set_value('allref', refconfig)
        auto_byr = AutoPT_BYR()
        refconfig['ref']['byr'] = auto_byr
        auto_tju = AutoPT_TJU()
        refconfig['ref']['tju'] = auto_tju
        auto_pter = AutoPT_PTER()
        refconfig['ref']['pter'] = auto_pter
        auto_mteam = AutoPT_MTEAM()
        refconfig['ref']['mteam'] = auto_mteam
        auto_pthome = AutoPT_PTHOME()
        refconfig['ref']['pthome'] = auto_pthome
        auto_frds = AutoPT_FRDS()
        refconfig['ref']['frds'] = auto_frds
        auto_ttg = AutoPT_TTG()
        refconfig['ref']['ttg'] = auto_ttg

        if gl.get_value('config').switch('byr'):
            # auto_byr = AutoPT_BYR()
            if maxtime % gl.get_value('config').intervaltime('byr') != 0:
                maxtime *= gl.get_value('config').intervaltime('byr')
        if gl.get_value('config').switch('tju'):
            # auto_tju = AutoPT_TJU()
            if maxtime % gl.get_value('config').intervaltime('tju') != 0:
                maxtime *= gl.get_value('config').intervaltime('tju')
        if gl.get_value('config').switch('pter'):
            # auto_pter = AutoPT_PTER()
            if maxtime % gl.get_value('config').intervaltime('pter') != 0:
                maxtime *= gl.get_value('config').intervaltime('pter')
        if gl.get_value('config').switch('mteam'):
            # auto_mteam = AutoPT_MTEAM()
            if maxtime % gl.get_value('config').intervaltime('mteam') != 0:
                maxtime *= gl.get_value('config').intervaltime('mteam')
        if gl.get_value('config').switch('pthome'):
            # auto_pthome = AutoPT_PTHOME()
            if maxtime % gl.get_value('config').intervaltime('pthome') != 0:
                maxtime *= gl.get_value('config').intervaltime('pthome')
        if gl.get_value('config').switch('frds'):
            # auto_pthome = AutoPT_FRDS()
            if maxtime % gl.get_value('config').intervaltime('frds') != 0:
                maxtime *= gl.get_value('config').intervaltime('frds')
        if gl.get_value('config').switch('ttg'):
            # auto_pthome = AutoPT_TTG)
            if maxtime % gl.get_value('config').intervaltime('ttg') != 0:
                maxtime *= gl.get_value('config').intervaltime('ttg')

        manager = Manager()
        if maxtime % (6 * 3600) != 0:
            maxtime *= (6 * 3600)

        counttime = 0
        while gl.get_value('thread_flag'):
            if gl.get_value('config').switch('reseed') and counttime % 120 == 0:
                manager.checkalltorrentexist()
                manager.recheck()
            if gl.get_value('config').switch('reseed') and counttime % (6 * 3600) == 0:
                manager.checkprttracker()
                manager.recheckall()
                manager.checkemptydir()
            if gl.get_value('thread_flag') and gl.get_value('config').switch('ttg') and counttime % gl.get_value(
                    'config').intervaltime('ttg') == 0:
                auto_ttg.start()
                pass
            if gl.get_value('thread_flag') and gl.get_value('config').switch('frds') and counttime % gl.get_value(
                    'config').intervaltime('frds') == 0:
                auto_frds.start()
                pass
            if gl.get_value('thread_flag') and gl.get_value('config').switch('pthome') and counttime % gl.get_value(
                    'config').intervaltime('pthome') == 0:
                auto_pthome.start()
            if gl.get_value('thread_flag') and gl.get_value('config').switch('mteam') and counttime % gl.get_value(
                    'config').intervaltime('mteam') == 0:
                auto_mteam.start()
            if gl.get_value('thread_flag') and gl.get_value('config').switch('tju') and counttime % gl.get_value(
                    'config').intervaltime('tju') == 0:
                auto_tju.start()
            if gl.get_value('thread_flag') and gl.get_value('config').switch('pter') and counttime % gl.get_value(
                    'config').intervaltime('pter') == 0:
                auto_pter.start()
            if gl.get_value('thread_flag') and gl.get_value('config').switch('byr') and counttime % gl.get_value(
                    'config').intervaltime('byr') == 0:
                auto_byr.start()

            counttime = (1 + counttime) % maxtime
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
    gl._init()
    gl.set_value('thread_flag', True)
    try:
        gl.set_value('config', Myconfig.Config())
        gl.set_value('logger', Mylogger.Mylogger())
        gl.set_value('wechat', iyuu(gl.get_value('config').token))
        gl.set_value('thread', Thread(target=run))
        app = BGIcon.MyWindows()
        gl.set_value('wxpython', app)

        gl.get_value('logger').logger.info('程序启动')
        gl.get_value('thread').start()

        app.MainLoop()
    except BaseException:
        traceback.print_exc(file=open('treace.txt', 'w+'))
        # gl.get_value('logger').logger.exception(traceback.format_exc())
    gl.set_value('thread_flag', False)
