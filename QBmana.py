import os
import time
import traceback
from os.path import join, getsize

import psutil
import requests

import Myconfig
import Mylogger
import globalvar as gl


class QBAPI(object):

    def __init__(self, config):
        self.logger = gl.get_value('logger').logger
        self.config = config

        self._root = 'http://' + self.config['qbaddr']
        self.logger.debug('QBAPI Init =' + self._root)

        self._session = requests.session()
        self._session.headers = {
            'User-Agent': 'Mozilla/5.0 AppleWebKit/537.36 Chrome/79.0.3945.16 Safari/537.36 Edg/79.0.309.11'
        }

        self.dynamiccapacity = self.config['capacity']

        self.maincategory = self.config['maincategory']
        self.subcategory = self.config['subcategory']
        self.checktrackerhttps = self.config['checktrackerhttps']
        self.diskletter = ''
        self.checkcategory()

    def checkcategory(self):
        if self.maincategory == '':
            self.logger.info('no maincategory')
            return
        info = self.get_url('/api/v2/torrents/categories')
        if info.status_code == 200:
            listjs = info.json()

            self.logger.info('maincategory:' + self.maincategory)
            if self.maincategory in listjs:
                self.diskletter = listjs[self.maincategory]['savePath'][0]
                self.logger.info('diskletter:' + self.diskletter)
            else:
                self.logger.error('category ' + self.maincategory + ' is not exist!!!!')
                exit(2)

            tempcategory = []
            self.logger.info('Befor filter subcategory:' + ','.join(self.subcategory))
            for val in self.subcategory:
                if val in listjs and listjs[val]['savePath'][0] == self.diskletter:
                    tempcategory.append(val)
            self.subcategory = tempcategory
            self.logger.info('After filter subcategory:' + ','.join(self.subcategory))
        else:
            self.logger.error('Error when get category list')

    def checksize(self, filesize):
        res = True
        if self.config['autoflag'] and self.config['capacity'] != 0:
            self.logger.info('QBAPI check filesize =' + str(filesize) + 'GB')

            gtl = self.gettorrentlist()
            nowtotalsize, pretotalsize = self.gettotalsize(gtl)
            self.logger.debug('nowtotalsize =' + str(nowtotalsize) + 'GB')
            self.logger.debug('pretotalsize =' + str(pretotalsize) + 'GB')

            diskremainsize = 1048576  # 设置无穷大的磁盘大小为1PB=1024*1024GB
            if self.diskletter != '':
                # 留出1G容量防止空间分配失败
                diskremainsize = self.getdiskleftsize(self.diskletter) - 1 - (pretotalsize - nowtotalsize)
                self.logger.debug('diskremainsize =' + str(diskremainsize) + 'GB')
            self.dynamiccapacity = self.config['capacity'] \
                if pretotalsize + diskremainsize > self.config['capacity'] else pretotalsize + diskremainsize
            self.logger.info('dynamiccapacity =' + str(self.dynamiccapacity) + 'GB')

            if filesize > self.dynamiccapacity:
                self.logger.warning('Too big !!! filesize(' + str(filesize) + 'GB) > dynamic capacity(' +
                                    str(self.dynamiccapacity) + 'GB)')
                return False

            stlist, res = self.selecttorrent(filesize, gtl, pretotalsize)
            if not self.deletetorrent(stlist):
                self.logger.error('Error when delete torrent')
                return False
        return res

    def diskdelay(self, fsize):
        # 根据删除的大小来判断删除时间
        t = int(fsize / 10) + 1  # 假设每删除10GB要1秒
        time.sleep(t)

    def deletetorrent(self, stlist):
        ret = True
        for val in stlist:
            filescount = self.gettorrentcontent(val[0])
            info = self.get_url('/api/v2/torrents/delete?hashes=' + val[0] + '&deleteFiles=true')
            if info.status_code == 200:
                self.logger.info('delete torrent success , torrent hash =' + str(val))
                # 每一个文件删除0.333秒
                time.sleep(filescount / 3)
                # self.diskdelay(val[1])
            else:
                ret = False
                self.logger.error(
                    'delete torrent error ,status code = ' + str(info.status_code) + ', torrent hash =' + str(val))
        return ret

    def gettotalsize(self, gtl):
        predict_sumsize = 0
        now_sumsize = 0
        for val in gtl:
            predict_sumsize += val['size']
            now_sumsize += val['size'] if val['progress'] == 1 else self.getdirsize(val['save_path'] + val['name'])
        now_sumsize /= (1024 * 1024 * 1024)
        predict_sumsize /= (1024 * 1024 * 1024)
        self.logger.debug('predict torrent sum size =' + str(predict_sumsize) + 'GB')
        self.logger.debug('now torrent sum size =' + str(now_sumsize) + 'GB')
        return now_sumsize, predict_sumsize

    def selecttorrent(self, filesize, gtl, totalsize):
        deletesize = totalsize + filesize - self.dynamiccapacity
        self.logger.info('deletesize = ' + str(deletesize) + 'GB')
        d_list = []
        now = time.time()

        # need delete
        if deletesize > 0 and len(gtl) > 0:
            # 不删除 keeptorrenttime 小时内下载的种子
            infinte_lastactivity = [val for val in gtl
                                    if val['last_activity'] > now and
                                    now - val['added_on'] > self.config['keeptorrenttime'] * 60 * 60]
            infinte_lastactivity.sort(key=lambda x: x['added_on'])
            # print (infinte_lastactivity)
            for val in infinte_lastactivity:
                d_list.append([val['hash'], val['size'] / 1024 / 1024 / 1024])
                deletesize -= val['size'] / 1024 / 1024 / 1024
                self.logger.info(
                    'select torrent name:\"' + val['name'] + '\"  size=' + str(val['size'] / 1024 / 1024 / 1024) + 'GB')
                if deletesize < 0:
                    break
            self.logger.info('torrent select part 1 , list len = ' + str(len(d_list)))
        if deletesize > 0 and len(gtl) > 0:
            # 不删除 keeptorrenttime 小时内下载的种子
            other_lastactivity = [val for val in gtl
                                  if val['last_activity'] <= now and
                                  now - val['added_on'] > self.config['keeptorrenttime'] * 60 * 60]
            other_lastactivity.sort(key=lambda x: x['last_activity'])
            for val in other_lastactivity:
                d_list.append([val['hash'], val['size'] / 1024 / 1024 / 1024])
                deletesize -= val['size'] / 1024 / 1024 / 1024
                self.logger.info(
                    'select torrent name:\"' + val['name'] + '\"  size=' + str(val['size'] / 1024 / 1024 / 1024) + 'GB')
                if deletesize < 0:
                    break
            self.logger.info('torrent select part 2 , list len = ' + str(len(d_list)))
        if deletesize > 0:
            self.logger.info('deletesize > 0, 不满足条件, 不删除')
            d_list = []
            return d_list, False
        else:
            return d_list, True

    def gettorrentlist(self):
        listjs = []
        if self.maincategory != '':
            info = self.get_url('/api/v2/torrents/info?category=' + self.maincategory)
            self.logger.debug('get list status code = ' + str(info.status_code))
            if info.status_code == 200:
                listjs = info.json()
            for val in self.subcategory:
                info = self.get_url('/api/v2/torrents/info?category=' + val)
                self.logger.debug('get ' + val + ' list status code = ' + str(info.status_code))
                if info.status_code == 200:
                    templistjs = info.json()
                    listjs += templistjs
        else:
            info = self.get_url('/api/v2/torrents/info?sort=last_activity')
            self.logger.debug('get list status code = ' + str(info.status_code))
            if info.status_code == 200:
                listjs = info.json()
        return listjs

    def istorrentexist(self, thash):
        info = self.get_url('/api/v2/torrents/info?hashes=' + thash)
        self.logger.debug('Is torrent exist status code = ' + str(info.status_code))
        if info.status_code == 200:
            listjs = info.json()
            return len(listjs) > 0
        return False

    def gettorrentdlstatus(self, thash):
        info = self.get_url('/api/v2/torrents/info?hashes=' + thash)
        self.logger.debug('status code = ' + str(info.status_code))
        if info.status_code == 200:
            listjs = info.json()
            tstate = listjs[0]['state']
            self.logger.debug('torrent state:' + tstate)
            if tstate in ['downloading', 'pausedDL', 'queuedDL', 'uploading', 'pausedUP', 'queuedUP', 'stalledUP',
                          'forcedUP', 'stalledDL', 'forceDL']:
                return True
            else:
                # error missingFiles checkingUP allocating metaDL checkingDL checkingResumeData moving unknown
                return False
        elif info.status_code == 404:
            self.logger.error('Torrent hash was not found')

        return False

    def istorrentdlcom(self, thash):
        info = self.get_url('/api/v2/torrents/info?hashes=' + thash)
        self.logger.debug('status code = ' + str(info.status_code))
        if info.status_code == 200:
            listjs = info.json()
            if listjs[0]['completion_on'] != 4294967295:
                return True
            else:
                return False
        elif info.status_code == 404:
            self.logger.error('Torrent hash was not found')

    def gettorrentname(self, thash):
        info = self.get_url('/api/v2/torrents/info?hashes=' + thash)
        self.logger.debug('status code = ' + str(info.status_code))
        if info.status_code == 200:
            listjs = info.json()
            tname = listjs[0]['name']
            self.logger.debug('torrent name:' + tname)
            return tname
        elif info.status_code == 404:
            self.logger.error('Torrent hash was not found')
        return ''

    def gettorrenttracker(self, thash):
        info = self.get_url('/api/v2/torrents/trackers?hash=' + thash)
        self.logger.debug('status code = ' + str(info.status_code))
        if info.status_code == 200:
            listjs = info.json()
            tracker = [val['url'] for val in listjs if val['status'] != 0]
            # self.logger.debug('tracker:' + '\n'.join(tracker))
            return tracker
        elif info.status_code == 404:
            self.logger.error('Torrent hash was not found')
            return []

    def gettorrentcontent(self, thash):
        info = self.get_url('/api/v2/torrents/files?hash=' + thash)
        self.logger.debug('status code = ' + str(info.status_code))
        if info.status_code == 200:
            listjs = info.json()
            filescount = len(listjs)
            self.logger.debug('filescount:' + str(filescount))
            return filescount
        elif info.status_code == 404:
            self.logger.error('Torrent hash was not found')
        # 默认只有一个文件
        return 1

    def edittorrenttracker(self, thash, origin, new):
        info = self.get_url('/api/v2/torrents/editTracker?hash=' + thash +
                            '&origUrl=' + origin + '&newUrl=' + new)
        self.logger.debug('status code = ' + str(info.status_code))
        if info.status_code == 200:
            return True
        elif info.status_code == 400:
            self.logger.error('newUrl is not a valid URL')
        elif info.status_code == 404:
            self.logger.error('Torrent hash was not found')
        elif info.status_code == 409:
            self.logger.error('newUrl already exists for the torrent or origUrl was not found')
        return False

    def checktorrenttracker(self, thash):
        trackers = self.gettorrenttracker(thash)
        for val in trackers:
            if val.find('https') != 0 and val.find('http') == 0:
                new = val[:4] + 's' + val[4:]
                self.edittorrenttracker(thash, val, new)
                self.logger.error('更新tracker的http为https')

    def get_url(self, url):
        """Return BeautifulSoup Pages
        :url: page url
        :returns: BeautifulSoups
        """
        # self.logger.debug('Get url: ' + url)
        trytime = 3
        while trytime > 0:
            try:
                req = self._session.get(self._root + url, timeout=(30, 30))
                return req
            except BaseException as e:
                self.logger.exception(traceback.format_exc())
                trytime -= 1
                time.sleep(30)

    def post_url(self, url, data):
        """Return BeautifulSoup Pages
        :url: page url
        :returns: BeautifulSoups
        """
        # self.logger.debug('Get url: ' + url)
        trytime = 3
        while trytime > 0:
            try:
                req = self._session.post(self._root + url, files=data, timeout=(30, 30))
                return req
            except BaseException as e:
                self.logger.exception(traceback.format_exc())
                trytime -= 1
                time.sleep(30)

    def addtorrent(self, content, thash, tsize):
        data = {'torrents': content}
        # 判断种子是否存在
        if not self.istorrentexist(thash):
            # 分配空间失败
            if not self.checksize(tsize):
                return
            info = self.post_url('/api/v2/torrents/add', data)
            self.logger.debug('addtorrent status code = ' + str(info.status_code))

            if info.status_code == 200:
                self.logger.info('addtorrent  successfully info hash = ' + thash)

                # info = self.get_url('/api/v2/torrents/info?sort=added_on&reverse=true')
                #
                # if info.status_code == 200:
                #     hash = info.json()[0]['hash']
                self.settorrentcategory(thash)

                # 防止磁盘卡死,当磁盘碎片太多或磁盘负载重时此处会卡几到几十分钟
                while not self.gettorrentdlstatus(thash):
                    time.sleep(5)

                # 删除匹配的tracker,暂时每个种子都判断不管是哪个站点
                self.removematchtracker(thash, 'pttrackertju.tjupt.org')

                if self.checktrackerhttps:
                    self.checktorrenttracker(thash)
                self.resumetorrents(thash)
                # else:
                #     self.logger.eroor('获取种子hash失败')
            else:
                self.logger.error('addtorrent Error status code = ' + str(info.status_code))
        else:
            self.logger.warning('torrent already exist hash=' + thash)

    def settorrentcategory(self, thash):
        if self.maincategory != '':
            info = self.get_url('/api/v2/torrents/setCategory?hashes=' + thash + '&category=' + self.maincategory)
            if info.status_code == 200:
                self.logger.info('set category successfully')
            else:
                self.logger.error('set category ERROR')

    # 返回单位大小为Byte
    def getdirsize(self, tdir):
        size = 0
        if os.path.isdir(tdir):
            for root, dirs, files in os.walk(tdir):
                size += sum([getsize(join(root, name)) for name in files])
        elif os.path.isfile(tdir):
            size += getsize(tdir)
        elif os.path.isfile(tdir + '.!qB'):
            size += getsize(tdir + '.!qB')
        return size

    def getdiskleftsize(self, diskletter):
        p = psutil.disk_usage(diskletter + ':\\')[2] / 1024 / 1024 / 1024
        # self.logger.info(self.diskletter + '盘剩余空间' + str(p) + 'GB')
        return p

    def getqbtpreferences(self):
        info = self.get_url('/api/v2/app/preferences')
        if info.status_code == 200:
            self.logger.debug('get preferences successfully')
            listjs = info.json()
            return listjs
        # qbt web访问失败
        exit(3)

    def resumetorrents(self, thash):
        info = self.get_url('/api/v2/torrents/resume?hashes=' + thash)
        if info.status_code == 200:
            self.logger.debug('resume torrents successfully')
            return True

    def checktorrentdtanddd(self, thash):
        ret = True
        if not self.istorrentdlcom(thash):
            ret = self.deletetorrent(thash)
        return ret

    def removematchtracker(self, thash, trackerstr):
        trackerlist = self.gettorrenttracker(thash)
        for val in trackerlist:
            if trackerstr in val:
                self.removetorrenttracker(thash, val)

    def removetorrenttracker(self, thash, url):
        info = self.get_url('/api/v2/torrents/removeTrackers?hash=' + thash + '&urls=' + url)
        if info.status_code == 200:
            self.logger.debug('remove tracker successfully')
            return True
        elif info.status_code == 409:
            self.logger.error('All urls were not found')
        elif info.status_code == 404:
            self.logger.error('Torrent hash was not found')
        else:
            self.logger.error('Unknow error')
        return True


if __name__ == '__main__':
    gl._init()
    config = Myconfig.Config()['BYR']
    gl.set_value('config', config)
    gl.set_value('logger', Mylogger.Mylogger())
    api = QBAPI(config)
    # api.gettorrentcontent('518c06ad1a248bf5d042c226cd70a1707b187b79')
    api.checksize(123)
