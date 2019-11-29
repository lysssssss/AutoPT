import os
import time
from os.path import join, getsize

import psutil
import requests

import Myconfig
import Mylogger
import globalvar as gl


class QBAPI(object):

    def __init__(self):
        self.logger = gl.get_value('logger').logger

        self._root = 'http://' + gl.get_value('config').qbaddr
        self.logger.info('QBAPI Init =' + self._root)

        self._session = requests.session()
        self._session.headers = {
            'User-Agent': 'Mozilla/5.0 AppleWebKit/537.36 Chrome/79.0.3945.16 Safari/537.36 Edg/79.0.309.11'
        }

        self.dynamiccapacity = gl.get_value('config').capacity

        self.maincategory = gl.get_value('config').maincategory
        self.subcategory = gl.get_value('config').subcategory
        self.checktrackerhttps = gl.get_value('config').checktrackerhttps
        self.diskletter = ''
        self.checkcategory()
        self.incomplete_files_ext = self.getincomplete_files_ext()

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
        if gl.get_value('config').autoflag and gl.get_value('config').capacity != 0:
            self.logger.info('QBAPI check filesize =' + str(filesize) + 'GB')

            gtl = self.gettorrentlist()
            nowtotalsize, pretotalsize = self.gettotalsize(gtl)
            self.logger.debug('nowtotalsize =' + str(nowtotalsize) + 'GB')
            self.logger.debug('pretotalsize =' + str(pretotalsize) + 'GB')

            diskremainsize = 1048576  # 设置无穷大的磁盘大小为1PB=1024*1024GB
            if self.diskletter != '':
                # 留出1G容量防止空间分配失败
                diskremainsize = self.getdiskleftsize(self.diskletter) - 1 - (pretotalsize - nowtotalsize)
                self.logger.info('diskremainsize =' + str(diskremainsize) + 'GB')
            self.dynamiccapacity = gl.get_value('config').capacity \
                if pretotalsize + diskremainsize > gl.get_value('config').capacity else pretotalsize + diskremainsize
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
                # 每一个文件删除1秒
                time.sleep(filescount)
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
        self.logger.info('predict torrent sum size =' + str(predict_sumsize) + 'GB')
        self.logger.info('now torrent sum size =' + str(now_sumsize) + 'GB')
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
                                    now - val['added_on'] > gl.get_value('config').keeptorrenttime * 60 * 60]
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
                                  now - val['added_on'] > gl.get_value('config').keeptorrenttime * 60 * 60]
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
            # To be determined: stalledUP
            if tstate in ['downloading', 'pausedDL', 'queuedDL', 'uploading', 'pausedUP', 'queuedUP', 'stalledUP',
                          'forcedUP', 'stalledDL', 'forceDL']:
                return True
            else:
                # error missingFiles checkingUP allocating metaDL checkingDL checkingResumeData moving unknown
                return False
        elif info.status_code == 404:
            self.logger.error('Torrent hash was not found')

        return False

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
            self.logger.debug('tracker:' + '\n'.join(tracker))
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
                req = self._session.get(self._root + url)
                return req
            except BaseException as e:
                self.logger.error(e)
                trytime -= 1
                time.sleep(20)

    def post_url(self, url, data):
        """Return BeautifulSoup Pages
        :url: page url
        :returns: BeautifulSoups
        """
        # self.logger.debug('Get url: ' + url)
        trytime = 3
        while trytime > 0:
            try:
                req = self._session.post(self._root + url, files=data)
                return req
            except BaseException as e:
                self.logger.error(e)
                trytime -= 1
                time.sleep(20)

    def addtorrent(self, content, thash):
        data = {'torrents': content}
        if not self.istorrentexist(thash):
            info = self.post_url('/api/v2/torrents/add', data)
            self.logger.debug('addtorrent status code = ' + str(info.status_code))

            if info.status_code == 200:
                self.logger.info('addtorrent  successfully info hash = ' + thash)

                # info = self.get_url('/api/v2/torrents/info?sort=added_on&reverse=true')
                #
                # if info.status_code == 200:
                #     hash = info.json()[0]['hash']
                self.settorrentcategory(thash)

                # 防止磁盘卡死,当磁盘碎片太多时此处会卡几到几十分钟
                while not self.gettorrentdlstatus(thash):
                    time.sleep(5)
                if self.checktrackerhttps:
                    self.checktorrenttracker(thash)
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
            self.logger.info('get preferences successfully')
            listjs = info.json()
            return listjs
        # qbt web访问失败
        exit(3)

    def getincomplete_files_ext(self):
        return self.getqbtpreferences()['incomplete_files_ext']


if __name__ == '__main__':
    gl._init()
    gl.set_value('config', Myconfig.Config())
    gl.set_value('logger', Mylogger.Mylogger())
    api = QBAPI()
    # api.gettorrentcontent('518c06ad1a248bf5d042c226cd70a1707b187b79')
    # print('getdirsize' + str(api.getdirsize('E:\PT Downloads\Seven Seconds S01 2160p NF WEB-DL HEVC 10bit HDR DDP5.1-TrollUHD')))
    api.checksize(123)
