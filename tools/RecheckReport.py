# -*- coding: utf-8 -*-
# @Time    : 2020/1/21 23:19
# @Author  : Eason Li
# @GitHub  : https://github.com/lysssssss
# @File    : RecheckReport.py
# @Software: PyCharm

class RecheckReport:
    def __init__(self):
        self.dlmiss = 0
        self.jying = 0
        self.dlcom = 0
        self.dldel = 0
        self.dlouttime = 0
        self.listlen = 0
        self.jyfail = 0
        self.jysucc = 0
        self.dling = 0
        self.dllen = 0
        self.dltors = 0
        self.rslen = 0
        self.rsmiss = 0

    def init(self):
        self.dlcom = 0
        self.dling = 0
        self.dlmiss = 0
        self.dltors = 0
        self.dldel = 0
        self.dlouttime = 0

        self.listlen = 0
        self.dllen = 0
        self.rslen = 0

        self.rsmiss = 0
        self.jyfail = 0
        self.jysucc = 0
        self.jying = 0

    def __str__(self):
        return '\n' + \
               '检查种子数:' + str(self.listlen) + '\n' + \
               '下载数' + str(self.dllen) + '(下载完成' + str(self.dlcom) + ',下载中' + str(self.dling) + ',转辅种' \
               + str(self.dltors) + ',站点删除' + str(self.dldel) + ',下载超时' + str(self.dlouttime) + ',下载丢失' \
               + str(self.dlmiss) + ')\n' + \
               '辅种数' + str(self.rslen) + '(校验完成' + str(self.jysucc) + ',校验失败' + str(self.jyfail) + ',正在校验' \
               + str(self.jying) + ',丢失' + str(self.rsmiss) + ')\n'


class RecheckAllReport:
    def __init__(self):
        self.inquerynum = 0
        self.rsnum = 0
        self.yfznum = 0
        self.fzingnum = 0
        self.newfznum = 0
        self.nofznum = 0
        self.succnum = 0
        self.failnum = 0
        self.resnum = 0
        self.availablenum = 0

    def init(self):
        self.inquerynum = 0
        self.rsnum = 0
        self.yfznum = 0
        self.fzingnum = 0
        self.newfznum = 0
        self.nofznum = 0
        self.succnum = 0
        self.failnum = 0
        self.resnum = 0
        self.availablenum = 0

    def __str__(self):
        return '\n\n' + \
               '全辅种结束.\n' + \
               '查询辅种数:' + str(self.inquerynum) + '. 返回辅种数:' + str(self.resnum) + '.\n' + \
               '可辅种:' + str(self.availablenum) + '. 无辅种:' + str(self.nofznum) + '.\n' + \
               '总辅种数:' + str(self.rsnum) + '.已辅种:' + str(self.yfznum) + '. 正在辅种:' + str(self.fzingnum) + \
               '. 新添加辅种:' + str(self.newfznum) + '. 成功辅种:' + str(self.succnum) + '. 失败辅种:' + str(self.failnum) + \
               '\n'


def checkDirReport(dirinfo):
    retstr = '\n'
    if dirinfo['filesnum'] != 0:
        retstr = retstr + '辅种目录里有' + str(dirinfo['filesnum']) + '个文件' + '\n'
    retstr = retstr + '辅种目录数:' + str(dirinfo['notemptynum']) + '\n'
    retstr = retstr + 'QB辅种数:' + str(dirinfo['qbrsnum']) + '\n'
    if dirinfo['notemptynum'] != dirinfo['qbrsnum']:
        retstr += '！！！辅种目录数和QB辅种数不一致！！！'
    retstr = retstr + '清除空目录' + str(dirinfo['emptynum']) + '个' + '\n'
    return retstr
