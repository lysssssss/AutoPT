# -*- coding: utf-8 -*-
# @Time    : 2020/1/13 15:34
# @Author  : Eason Li
# @GitHub  : https://github.com/lysssssss
# @File    : sid.py.py
# @Software: PyCharm


sidlist = {
    3: 'mteam',
    5: 'tju',
    6: 'pter',
    45: 'byr',
}


def getsidname(sid):
    if not isinstance(sid, str):
        sid = int(sid)
    return sidlist[sid]


def getnamesid(name):
    name = name.lower()
    for key, value in sidlist.items():
        if value == name:
            return key
    return -1


def supportsid(sid):
    return sid in sidlist
