# -*- coding: utf-8 -*-
# @Time    : 2020/2/2 1:33
# @Author  : Eason Li
# @GitHub  : https://github.com/lysssssss
# @File    : dirmanager.py
# @Software: PyCharm
import os
import shutil


def isdirempty(path):
    files = os.listdir(path)  # 查找路径下的所有的文件夹及文件
    for file in files:
        if os.path.isdir(path + '\\' + file):
            if not isdirempty(path + '\\' + file):
                return False
        else:
            return False
    return True


def deletedir(dirlist):
    if isinstance(dirlist, str):
        dirlist = [dirlist]
    for val in dirlist:
        try:
            shutil.rmtree(val)
        except FileNotFoundError as e:
            pass


def getemptydirlist(path):
    empty = 0
    notempty = 0
    filesnum = 0
    emptylist = []
    if not path.endswith('\\'):
        path = path + '\\'
    if os.path.exists(path):
        files = os.listdir(path)  # 查找路径下的所有的文件夹及文件
        for file in files:
            if os.path.isdir(path + file):
                if isdirempty(path + file):  # 判断文件夹是否为空
                    empty += 1
                    emptylist.append(path + file)
                else:
                    notempty += 1
            else:
                filesnum += 1
    return {
        'emptynum': empty,
        'notemptynum': notempty,
        'filesnum': filesnum,
        'emptylist': emptylist
    }
