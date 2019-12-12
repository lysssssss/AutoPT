import json
import os

from jsmin import jsmin


class Config(object):
    """read config"""

    def __getitem__(self, key):
        if key.upper() == 'BYR':
            return self.byrconfig
        elif key.upper() == 'TJU':
            return self.tjuconfig
        elif key.upper() == 'PTER':
            return self.pterconfig
        return {}

    def __init__(self):
        self.byrconfig = {
            'switch': False,
            'checktrackerhttps': False,
            'checkptmode': 1,
            'maincategory': '',
            'subcategory': [],
            'qbaddr': '',
            'capacity': 0,
            'capacityuint': 'GB',
            'capacitynum': 0,
            'dlroot': '',
            'autoflag': False,
            'intervaltime': 60,
            'keeptorrenttime': 0,
            'root': 'https://bt.byr.cn/'
        }
        self.tjuconfig = {
            'switch': False,
            'checktrackerhttps': False,
            'checkptmode': 1,
            'maincategory': '',
            'subcategory': [],
            'qbaddr': '',
            'capacity': 0,
            'capacityuint': 'GB',
            'capacitynum': 0,
            'dlroot': '',
            'autoflag': False,
            'intervaltime': 60,
            'keeptorrenttime': 0,
            'root': 'https://www.tjupt.org/'
        }
        self.pterconfig = {
            'switch': False,
            'checktrackerhttps': False,
            'checkptmode': 1,
            'maincategory': '',
            'subcategory': [],
            'qbaddr': '',
            'capacity': 0,
            'capacityuint': 'GB',
            'capacitynum': 0,
            'dlroot': '',
            'autoflag': False,
            'intervaltime': 60,
            'keeptorrenttime': 0,
            'root': 'https://pterclub.com/'
        }
        if os.path.exists('config.json'):
            f = open('config.json', 'r', encoding='utf-8')
            text = jsmin(f.read())
            # text = f.read()
            f.close()
            paras = json.loads(text)
            self.readqbtconfig(paras)
            self.readlogconfig(paras)
            self.readbyrconfig(paras)
            self.readtjuconfig(paras)
            self.readpterconfig(paras)
        else:
            self._logsavetime = 7
            self._loglevel = 'info'

    def transcapacity(self, config):
        if config['capacityuint'] == 'GB':
            config['capacity'] = config['capacitynum']
        elif config['capacityuint'] == 'TB':
            config['capacity'] = config['capacitynum'] * 1024
        elif config['capacityuint'] == 'MB':
            config['capacity'] = config['capacitynum'] / 1024
        else:
            config['capacity'] = 0

    def readbyrconfig(self, param):
        if 'BYR' in param:
            paras = param['BYR']
            self.readcommonconfig(paras, self.byrconfig)
            # To add custom config here

    def readtjuconfig(self, param):
        if 'TJU' in param:
            paras = param['TJU']
            self.readcommonconfig(paras, self.tjuconfig)
            # To add custom config here

    def readpterconfig(self, param):
        if 'PTER' in param:
            paras = param['PTER']
            self.readcommonconfig(paras, self.pterconfig)
            # To add custom config here

    def readcommonconfig(self, paras, pt_config):
        if 'switch' in paras:
            pt_config['switch'] = paras['switch']
        if 'torrent_download_root' in paras:
            pt_config['dlroot'] = paras['torrent_download_root']
            if not pt_config['dlroot'].endswith('/'):
                pt_config['dlroot'] = pt_config['dlroot'] + '/'
        if 'Auto_management' in paras:
            pt_config['autoflag'] = paras['Auto_management']
        if 'IntervalTime' in paras:
            pt_config['intervaltime'] = paras['IntervalTime']
        if 'CapacityNum' in paras:
            pt_config['capacitynum'] = paras['CapacityNum'] if paras['CapacityNum'] > -1 else 10485760
        if 'QB_WebAddr' in paras:
            pt_config['qbaddr'] = paras['QB_WebAddr']
        if 'CapacityUint' in paras:
            pt_config['capacityuint'] = paras['CapacityUint'].upper() \
                if paras['CapacityUint'].upper() in ['GB', 'TB'] else 'GB'
        if 'MainCategory' in paras:
            pt_config['maincategory'] = paras['MainCategory'][0] if len(paras['MainCategory'][:1]) > 0 else ''
            pt_config['subcategory'] = paras['MainCategory'][1:]
            pt_config['subcategory'] = list(set(pt_config['subcategory']))
        if 'CheckPTMode' in paras:
            pt_config['checkptmode'] = paras['CheckPTMode'] if paras['CheckPTMode'] in [1, 2] else 1
        if 'KeepTorrentTime' in paras:
            pt_config['keeptorrenttime'] = paras['KeepTorrentTime'] if paras['KeepTorrentTime'] >= 0 else 0

        if 'CheckTrackerHTTPS' in paras:
            pt_config['checktrackerhttps'] = paras['CheckTrackerHTTPS']
        # 转换磁盘容量
        self.transcapacity(pt_config)
        # 处理异常情况，强制关闭磁盘管理
        if pt_config['capacitynum'] == 0:
            pt_config['autoflag'] = False

    def readlogconfig(self, para):
        if 'log' in para:
            paras = para['log']
            if 'LogLevel' in paras:
                self._loglevel = paras['LogLevel'].lower()
                self._loglevel = self._loglevel if self._loglevel in ['info', 'debug'] else 'info'
            else:
                self._loglevel = 'info'
            if 'LogSaveTime' in paras:
                self._logsavetime = paras['LogSaveTime']
            else:
                self._logsavetime = 7
        else:
            self._loglevel = 'info'
            self._logsavetime = 7

    def readqbtconfig(self, para):
        if 'qbt' in para:
            paras = para['qbt']
            if 'path' in paras:
                self._qbtpath = paras['path']
            else:
                self._qbtpath = ''
        else:
            self._qbtpath = ''

    def getnameconfig(self):
        return {
            'BYR': self.byrconfig,
            'TJU': self.tjuconfig,
            'PTER': self.pterconfig
        }

    def switch(self, name):
        return self.getnameconfig()[name.upper()]['switch']

    def checktrackerhttps(self, name):
        return self.getnameconfig()[name.upper()]['checktrackerhttps']

    def keeptorrenttime(self, name):
        return self.getnameconfig()[name.upper()]['keeptorrenttime']

    def checkptmode(self, name):
        return self.getnameconfig()[name.upper()]['checkptmode']

    def maincategory(self, name):
        return self.getnameconfig()[name.upper()]['maincategory']

    def subcategory(self, name):
        return self.getnameconfig()[name.upper()]['subcategory']

    def qbaddr(self, name):
        return self.getnameconfig()[name.upper()]['qbaddr']

    def capacity(self, name):
        return self.getnameconfig()[name.upper()]['capacity']

    def dlroot(self, name):
        return self.getnameconfig()[name.upper()]['dlroot']

    def autoflag(self, name):
        return self.getnameconfig()[name.upper()]['autoflag']

    def intervaltime(self, name):
        return self.getnameconfig()[name.upper()]['intervaltime']

    @property
    def qbtpath(self):
        return self._qbtpath

    @property
    def loglevel(self):
        return self._loglevel

    @property
    def logsavetime(self):
        return self._logsavetime


if __name__ == '__main__':
    config = Config()
    print(config['BYR'])
    pass
