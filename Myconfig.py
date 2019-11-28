import json
from jsmin import jsmin
import os


class Config(object):
    """read config"""

    def __init__(self):
        if os.path.exists('config.json'):
            f = open('config.json', 'r', encoding='utf-8')
            text = jsmin(f.read())
            # text = f.read()
            f.close()
            paras = json.loads(text)
            if 'torrent_download_root' in paras:
                self._dlroot = paras['torrent_download_root']
                if not self._dlroot.endswith('/'):
                    self._dlroot = self._dlroot + '/'
            else:
                self._dlroot = ''
            if 'Auto_management' in paras:
                self._auto_flag = paras['Auto_management']
            else:
                self._auto_flag = False
            if 'test' in paras:
                self.test = paras['test']
            else:
                self.test = ''
            if 'IntervalTime' in paras:
                self._intervaltime = paras['IntervalTime']
            else:
                self._intervaltime = 60
            if 'username' in paras:
                self._username = paras['username']
            else:
                self._username = ''
            if 'password' in paras:
                self._password = paras['password']
            else:
                self._password = ''
            if 'CapacityNum' in paras:
                self._capacitynum = paras['CapacityNum'] if paras['CapacityNum'] > -1 else 10485760
            else:
                self._capacitynum = 0
            if 'QB_WebAddr' in paras:
                self._qbaddr = paras['QB_WebAddr']
            else:
                self._qbaddr = ''
            if 'CapacityUint' in paras:
                self._capacityuint = paras['CapacityUint'].upper() if paras['CapacityUint'].upper() in ['GB',
                                                                                                        'TB'] else 'GB'
            else:
                self._capacityuint = 'GB'
            if 'MainCategory' in paras:
                self._maincategory = paras['MainCategory'][0] if len(paras['MainCategory'][:1]) > 0 else ''
                self._subcategory = paras['MainCategory'][1:]
                self._subcategory = list(set(self._subcategory))
            else:
                self._maincategory = ''
                self._subcategory = []
            if 'LogLevel' in paras:
                self._loglevel = paras['LogLevel'].lower()
                self._loglevel = self._loglevel if self._loglevel in ['info', 'debug'] else 'info'
            else:
                self._loglevel = 'info'
            if 'LogSaveTime' in paras:
                self._logsavetime = paras['LogSaveTime']
            else:
                self._logsavetime = 7
            if 'CheckPTMode' in paras:
                self._checkptmode = paras['CheckPTMode'] if paras['CheckPTMode'] in [1, 2] else 1
            else:
                self._checkptmode = 1
            if 'KeepTorrentTime' in paras:
                self._keeptorrenttime = paras['KeepTorrentTime'] if paras['KeepTorrentTime'] >= 0 else 0
            else:
                self._keeptorrenttime = 0
            if 'CheckTrackerHTTPS' in paras:
                self._checktrackerhttps = paras['CheckTrackerHTTPS']
            else:
                self._checktrackerhttps = False
        else:
            self._checktrackerhttps = False
            self._checkptmode = 1
            self._logsavetime = 7
            self._loglevel = 'info'
            self._maincategory = ''
            self._subcategory = []
            self._qbaddr = ''
            self._capacity = 0
            self._capacityuint = 'GB'
            self._capacitynum = 0
            self._dlroot = ''
            self._auto_flag = False
            self.test = ''
            self._intervaltime = 60
            self._username = ''
            self._password = ''
            self._keeptorrenttime = 0
        # 转换磁盘容量
        self.transcapacity()
        # 处理异常情况，强制关闭磁盘管理
        if self._capacitynum == 0:
            self._auto_flag = False

    def transcapacity(self):
        if self._capacityuint == 'GB':
            self._capacity = self._capacitynum
        elif self._capacityuint == 'TB':
            self._capacity = self._capacitynum * 1024
        elif self._capacityuint == 'MB':
            self._capacity = self._capacitynum / 1024
        else:
            self._capacity = 0

    @property
    def checktrackerhttps(self):
        return self._checktrackerhttps

    @property
    def keeptorrenttime(self):
        return self._keeptorrenttime

    @property
    def checkptmode(self):
        return self._checkptmode

    @property
    def loglevel(self):
        return self._loglevel

    @property
    def logsavetime(self):
        return self._logsavetime

    @property
    def maincategory(self):
        return self._maincategory

    @property
    def subcategory(self):
        return self._subcategory

    @property
    def qbaddr(self):
        return self._qbaddr

    @property
    def capacity(self):
        return self._capacity

    @property
    def dlroot(self):
        return self._dlroot

    @property
    def autoflag(self):
        return self._auto_flag

    @property
    def intervaltime(self):
        return self._intervaltime

    @property
    def username(self):
        return self._username

    @property
    def password(self):
        return self._password


if __name__ == '__main__':
    print(Config())
