# -*- coding: utf-8 -*-
# @Time    : 2020/1/29 5:56
# @Author  : Eason Li
# @GitHub  : https://github.com/lysssssss
# @File    : qbapi.py
# @Software: PyCharm
import time

import requests

import tools.globalvar as gl


class qbapi:
    def __init__(self, root):
        self._root = root
        self.logger = gl.get_value('logger').logger
        self._session = requests.session()
        self._session.headers = {
            'User-Agent': 'Mozilla/5.0 AppleWebKit/537.36 Chrome/79.0.3945.16 Safari/537.36 Edg/79.0.309.11'
        }

    def get_url(self, url):
        trytime = 3
        while trytime > 0:
            try:
                req = self._session.get(self._root + url, timeout=(5, 30))
                return req
            except BaseException as e:
                self.logger.debug(e)
                trytime -= 1
                time.sleep(5)

    def post_url(self, url, data=None, files=None):
        trytime = 3
        while trytime > 0:
            try:
                req = self._session.post(self._root + url, files=files, data=data, timeout=(5, 30))
                return req
            except BaseException as e:
                self.logger.debug(e)
                trytime -= 1
                time.sleep(5)

    def webapiVersion(self):
        info = self.get_url('/api/v2/app/webapiVersion')
        if info is None:
            pass
        elif info.status_code == 200:
            return info.content.decode()
        return ''

    def setCategory(self, thash, ctn):
        if isinstance(thash, list):
            thash = "|".join(thash)
        info = self.get_url('/api/v2/torrents/setCategory?hashes=' + thash + '&category=' + ctn)
        if info is None:
            pass
        elif info.status_code == 200:
            self.logger.debug('成功移动种子到' + ctn)
        elif info.status_code == 409:
            self.logger.error('Category name does not exist')
        else:
            self.logger.error('移动种子失败 未知错误')

    def setAutoManagement(self, thash, b):
        if isinstance(thash, list):
            thash = "|".join(thash)
        b = 'true' if b else 'false'
        info = self.get_url(
            '/api/v2/torrents/setAutoManagement?hashes=' + thash + '&enable=' + b)
        if info is None:
            pass
        elif info.status_code == 200:
            # self.logger.debug('成功关闭' + thash + '自动管理')
            pass
        else:
            self.logger.error('切换种子自动管理失败 未知错误')

    def torrentsInfo(self, hashes=None, category=None, sort=None, filter=None):
        fixurl = []
        if hashes is not None:
            if isinstance(hashes, list):
                hashes = "|".join(hashes)
                fixurl.append('hashes=' + hashes)
            elif isinstance(hashes, str):
                fixurl.append('hashes=' + hashes)
        if category is not None:
            fixurl.append('category=' + category)
        if sort is not None:
            fixurl.append('sort=' + sort)
        if filter is not None:
            fixurl.append('filter=' + filter)
        listjs = []
        info = self.get_url('/api/v2/torrents/info?' + "&".join(fixurl))
        if info is None:
            pass
        elif info.status_code == 200:
            listjs = info.json()
        return listjs

    def torrentInfo(self, thash):
        listjs = {}
        info = self.get_url('/api/v2/torrents/info?hashes=' + thash)
        if info is None:
            pass
        elif info.status_code == 200:
            listjs = info.json()
            if len(listjs) != 0:
                return listjs[0]
        return listjs

    def torrentTrackers(self, thash):
        listjs = []
        info = self.get_url('/api/v2/torrents/trackers?hash=' + thash)
        if info is None:
            pass
        elif info.status_code == 200:
            # listjs = info.json()
            # tracker = [val['url'] for val in listjs if val['status'] != 0]
            # self.logger.debug('tracker:' + '\n'.join(tracker))
            listjs = info.json()
        elif info.status_code == 404:
            self.logger.error('Torrent hash was not found')
        return listjs

    def removeTrackers(self, thash, trackerurl):
        info = self.get_url('/api/v2/torrents/removeTrackers?hash=' + thash + '&urls=' + trackerurl)
        if info is None:
            return False
        elif info.status_code == 200:
            self.logger.debug('remove tracker successfully')
            return True
        elif info.status_code == 409:
            self.logger.error('All urls were not found')
        elif info.status_code == 404:
            self.logger.error('Torrent hash was not found')
        else:
            self.logger.error('Unknow error')
        return False

    def setLocation(self, thash, spath):
        info = self.get_url('/api/v2/torrents/setLocation?hashes=' + thash + '&location=' + spath)
        if info is None:
            return False
        elif info.status_code == 200:
            self.logger.debug('成功移动种子到' + spath)
            return True
        elif info.status_code == 400:
            self.logger.error('Save path is empty ' + spath)
        elif info.status_code == 403:
            self.logger.error('User does not have write access to directory ' + spath)
        elif info.status_code == 409:
            self.logger.error('Unable to create save path directory ' + spath)
        else:
            self.logger.error('移动种子失败 未知错误')
        return False

    def torrentFiles(self, thash):
        listjs = []
        info = self.get_url('/api/v2/torrents/files?hash=' + thash)
        if info is None:
            pass
        elif info.status_code == 200:
            listjs = info.json()
        elif info.status_code == 404:
            self.logger.error('Torrent hash was not found')
        return listjs

    def editTracker(self, thash, origin, new):
        info = self.get_url('/api/v2/torrents/editTracker?hash=' + thash +
                            '&origUrl=' + origin + '&newUrl=' + new)
        if info is None:
            return False
        if info.status_code == 200:
            return True
        elif info.status_code == 400:
            self.logger.error('newUrl is not a valid URL')
        elif info.status_code == 404:
            self.logger.error('Torrent hash was not found')
        elif info.status_code == 409:
            self.logger.error('newUrl already exists for the torrent or origUrl was not found')
        return False

    def torrentsDelete(self, dellist, deldata=True):
        if isinstance(dellist, list):
            dellist = "|".join(dellist)
        deldata = 'true' if deldata else 'false'
        info = self.get_url(
            '/api/v2/torrents/delete?hashes=' + dellist + '&deleteFiles=' + deldata)
        if info is None:
            return False
        elif info.status_code == 200:
            return True
        return False

    def category(self):
        listjs = {}
        info = self.get_url('/api/v2/torrents/categories')
        if info is None:
            pass
        elif info.status_code == 200:
            listjs = info.json()
        return listjs

    def setTorrentsCategory(self, thash, category):
        if isinstance(thash, list):
            dellithashst = "|".join(thash)
        info = self.get_url('/api/v2/torrents/setCategory?hashes=' + thash + '&category=' + category)
        if info is None:
            return False
        elif info.status_code == 200:
            self.logger.info('set category successfully')
            return True
        elif info.status_code == 409:
            self.logger.error('Category name does not exist')
        return False

    def getApplicationPreferences(self):
        listjs = {}
        info = self.get_url('/api/v2/app/preferences')
        if info is None:
            pass
        elif info.status_code == 200:
            self.logger.debug('get preferences successfully')
            listjs = info.json()
        return listjs

    def addNewTorrentByBin(self, binary, paused=None, category=None, autoTMM=None, savepath=None, skip_checking=None,
                           upLimit=None):
        data = {}
        if paused is not None and isinstance(paused, bool):
            data['paused'] = paused
        if category is not None and isinstance(category, str):
            data['category'] = category
        if autoTMM is not None and isinstance(autoTMM, bool):
            data['autoTMM'] = autoTMM
        if savepath is not None and isinstance(savepath, str):
            data['savepath'] = savepath
        if skip_checking is not None and isinstance(skip_checking, bool):
            data['skip_checking'] = skip_checking
        if upLimit is not None and (isinstance(upLimit, int) or isinstance(upLimit, float)) and upLimit >= 0:
            data['upLimit'] = int(upLimit)
        info = self.post_url('/api/v2/torrents/add', files={'torrents': binary}, data=data)
        if info is None:
            return False
        elif info.status_code == 200:
            self.logger.info('addtorrent  successfully ')
            return True
        elif info.status_code == 415:
            self.logger.error('Torrent file is not valid')
        else:
            self.logger.error('addtorrent Error status code = ' + str(info.status_code))
        return False

    def resumeTorrents(self, hashes):
        if isinstance(hashes, list):
            hashes = "|".join(hashes)
        info = self.get_url('/api/v2/torrents/resume?hashes=' + hashes)
        if info is None:
            return False
        elif info.status_code == 200:
            self.logger.debug('resume torrents successfully')
            return True
        return False
