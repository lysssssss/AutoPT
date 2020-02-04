# -*- coding: utf-8 -*-
# @Time    : 2020/2/4 22:04
# @Author  : Eason Li
# @GitHub  : https://github.com/lysssssss
# @File    : iyuu.py
# @Software: PyCharm
import time

import requests

import tools.globalvar as gl


class iyuu:
    def __init__(self, token):
        self.token = token
        self._root = 'https://iyuu.cn/' + self.token + '.send'
        self._session = requests.session()
        self.logger = gl.get_value('logger').logger

    def post_url(self, data=None, files=None):
        trytime = 3
        while trytime > 0:
            try:
                req = self._session.post(self._root, files=files, data=data, timeout=(10, 10))
                return req
            except BaseException as e:
                trytime -= 1
                time.sleep(5)

    def send(self, text=None, desp=None):
        if text is None and desp is None:
            return False
        sendlist = {}
        if text is not None:
            sendlist['text'] = str(text)
        if desp is not None:
            sendlist['desp'] = str(desp)
        resp = self.post_url(data=sendlist)
        if resp.status_code == 200:
            ret = resp.json()
            if ret['errmsg'] != 'ok':
                self.logger.warning('发送失败.' + str(ret))
            else:
                return True
        else:
            self.logger.warning('发送失败,错误状态码'+str(resp.status_code))
        return False
