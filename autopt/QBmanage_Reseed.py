import json
import os
import time
from os.path import join, getsize

import psutil
import requests

import tools.globalvar as gl
from tools.RecheckReport import RecheckReport, RecheckAllReport
from tools.TorrentInfo import get_torrent_name
from tools.qbapi import qbapi
from tools.sid import supportsid, getsidname


class Manager(object):

    def __init__(self, config=None):
        basepath = 'autopt/appdata/'
        self.reseedcategory = 'Reseed'
        self.rechecklistname = basepath + 'ReChecklist.csv'
        self.reseedjsonname = basepath + 'ReSeedRecord.json'
        self.logger = gl.get_value('logger').logger
        self.qbapi = qbapi(gl.get_value('config').qbaddr)

        self.recheckreport = RecheckReport()
        self.recheckallreport = RecheckAllReport()

        self._session = requests.session()
        self._session.headers = {
            'User-Agent': 'Mozilla/5.0 AppleWebKit/537.36 Chrome/79.0.3945.16 Safari/537.36 Edg/79.0.309.11'
        }

        if config is not None and config['name'] != 'reseed':
            self.config = config
            self.dynamiccapacity = self.config['capacity']
            self.maincategory = self.config['maincategory']
            self.subcategory = self.config['subcategory']
            self.diskletter = ''
            self.getcategory()
        # else:
        # Reseed
        self.stationref = gl.get_value('allref')['ref']
        self.dlcategory = []
        self.allcategory = []
        self.getallcategory()

    def getallcategory(self):
        listjs = self.qbapi.category()

        for key, value in listjs.items():
            self.allcategory.append(key)
        allconfig = gl.get_value('config')['all']
        for key, value in allconfig.items():
            if value['switch']:
                if value['maincategory'] in self.allcategory and value['maincategory'] not in self.dlcategory:
                    self.dlcategory.append(value['maincategory'])
                for val in value['subcategory']:
                    if val in self.allcategory and val not in self.dlcategory:
                        self.dlcategory.append(val)

    def getcategory(self):
        if self.maincategory == '':
            self.logger.info('no maincategory')
            return
        listjs = self.qbapi.category()

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

    def checksize(self, filesize):
        res = True
        if self.config['capacity'] != 0:
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

    def deletetorrent(self, stlist, deleteFiles=True):
        ret = True
        if isinstance(stlist, str):
            stlist = [(stlist, [])]
        alllist = []
        filescount = 0
        for val in stlist:
            filescount += len(self.qbapi.torrentFiles(val[0]))
            alllist.append(val[0])
            alllist += val[1]
        if not self.qbapi.torrentsDelete(alllist, True):
            ret = False
        # 每个文件延迟0.2秒
        time.sleep(filescount / 5)
        # for val in alllist:
        #     filescount = len(self.qbapi.torrentfiles(val))
        #     self.logger.debug('filescount:' + str(filescount))
        #     info = self.get_url('/api/v2/torrents/delete?hashes=' + val + '&deleteFiles=' + str(deleteFiles))
        #     if info.status_code == 200:
        #         self.logger.info('deleting')
        #         # 每一个文件删除0.1秒
        #
        #         self.logger.info('delete torrent success , torrent hash =' + str(val))
        #         # self.diskdelay(val[1])
        #     else:
        #         ret = False
        #         self.logger.error(
        #             'delete torrent error ,status code = ' + str(info.status_code) + ', torrent hash =' + str(val))
        jsonlist = {}
        updatefile = False
        if len(stlist) and os.path.exists(self.reseedjsonname):
            jsonlist = {}
            with open(self.reseedjsonname, 'r', encoding='UTF-8')as f:
                jsonlist = json.loads(f.read())
            for val in stlist:
                if val[0] in jsonlist:
                    updatefile = True
                    del jsonlist[val[0]]
        if updatefile:
            with open(self.reseedjsonname, 'w', encoding='UTF-8')as f:
                f.write(json.dumps(jsonlist))

        newstr = ''
        updatefile = False
        if len(stlist) and os.path.exists(self.rechecklistname):
            with open(self.rechecklistname, 'r', encoding='UTF-8') as f:
                for line in f.readlines():
                    rct = line.strip().split(',')
                    if rct[3] in alllist:
                        updatefile = True
                    else:
                        newstr += line
        if updatefile:
            with open(self.rechecklistname, 'w', encoding='UTF-8') as f:
                f.write(newstr)

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
            # infinte_lastactivity.sort(key=lambda x: x['added_on'])
            # reseedhash
            infinte_lastactivity = self.sortfilterwithreseed(infinte_lastactivity, 'added_on')
            # print (infinte_lastactivity)
            for val in infinte_lastactivity:
                d_list.append((val['hash'], val['reseedlist']))
                deletesize -= val['size'] / 1024 / 1024 / 1024
                self.logger.info(
                    'select torrent name:\"' + val['name'] + '\"  size=' + str(
                        val['size'] / 1024 / 1024 / 1024) + 'GB, Reseed count:' + str(len(val['reseedlist'])))
                if deletesize < 0:
                    break
            self.logger.info('torrent select part 1 , list len = ' + str(len(d_list)))
        if deletesize > 0 and len(gtl) > 0:
            # 不删除 keeptorrenttime 小时内下载的种子
            other_lastactivity = [val for val in gtl
                                  if val['last_activity'] <= now and
                                  now - val['added_on'] > self.config['keeptorrenttime'] * 60 * 60]
            # other_lastactivity.sort(key=lambda x: x['last_activity'])
            #  reseedhash
            other_lastactivity = self.sortfilterwithreseed(other_lastactivity, 'last_activity')
            for val in other_lastactivity:
                d_list.append((val['hash'], val['reseedlist']))
                deletesize -= val['size'] / 1024 / 1024 / 1024
                self.logger.info(
                    'select torrent name:\"' + val['name'] + '\"  size=' + str(
                        val['size'] / 1024 / 1024 / 1024) + 'GB, Reseed count:' + str(len(val['reseedlist'])))
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
            info = self.qbapi.torrentsInfo(category=self.maincategory)
            listjs = info
            for val in self.subcategory:
                info = self.qbapi.torrentsInfo(category=val)
                listjs += info
        else:
            listjs = self.qbapi.torrentsInfo(sort='last_activity')
        return listjs

    def istorrentexist(self, thash):
        return len(self.qbapi.torrentInfo(thash)) > 0

    def gettorrentdlstatus(self, thash):
        tinfo = self.qbapi.torrentInfo(thash)
        # 修复程序速度太快QBAPI未能获取到种子信息
        if len(tinfo) == 0:
            return False
        tstate = tinfo['state']
        self.logger.debug('torrent state:' + tstate)
        if tstate in ['downloading', 'pausedDL', 'queuedDL', 'uploading', 'pausedUP', 'queuedUP', 'stalledUP',
                      'forcedUP', 'stalledDL', 'forceDL', 'checkingUP', 'checkingDL']:
            return True
        else:
            # error missingFiles allocating metaDL  checkingResumeData moving unknown
            return False

    def istorrentdlcom(self, thash):
        tinfo = self.qbapi.torrentInfo(thash)
        if len(tinfo) == 0:
            self.logger.debug('Cannot find torrent' + thash + '. Maybe already deleted')
            return False
        if tinfo['completion_on'] == 4294967295:
            return False
        else:
            return True

    def istorrentcheckcom(self, thash):
        tinfo = self.qbapi.torrentInfo(thash)
        if len(tinfo) == 0:
            self.logger.debug('Cannot find torrent' + thash + '. Maybe already deleted')
            return -1
        tstate = tinfo['state']
        self.logger.debug('torrent state:' + tstate)
        if tstate in ['downloading', 'pausedDL', 'queuedDL', 'stalledDL', 'forceDL', 'missingFiles', 'metaDL',
                      'allocating']:
            return 0
        elif tstate in ['checkingDL', 'checkingUP', 'checkingResumeData', 'moving']:
            return 1
        elif tstate in ['uploading', 'pausedUP', 'queuedUP', 'stalledUP', 'forcedUP']:
            return 2
        else:
            # error moving unknown
            return -1

    def gettorrentname(self, thash):
        tinfo = self.qbapi.torrentInfo(thash)
        if len(tinfo) == 0:
            return ''
        return tinfo['name']

    def gettorrentcategory(self, thash):
        tinfo = self.qbapi.torrentInfo(thash)
        if len(tinfo) == 0:
            return ''
        return tinfo['category']
        # self.logger.debug('torrent category:' + tcategory)

    # def gettorrenttracker(self, thash):
    #     info = self.get_url('/api/v2/torrents/trackers?hash=' + thash)
    #     self.logger.debug('status code = ' + str(info.status_code))
    #     if info.status_code == 200:
    #         listjs = info.json()
    #         tracker = [val['url'] for val in listjs if val['status'] != 0]
    #         # self.logger.debug('tracker:' + '\n'.join(tracker))
    #         return tracker
    #     elif info.status_code == 404:
    #         self.logger.error('Torrent hash was not found')
    #         return []

    # def gettorrentcontent(self, thash):
    #     info = self.get_url('/api/v2/torrents/files?hash=' + thash)
    #     self.logger.debug('status code = ' + str(info.status_code))
    #     if info.status_code == 200:
    #         listjs = info.json()
    #         return listjs
    #     elif info.status_code == 404:
    #         self.logger.error('Torrent hash was not found')
    #     # 默认只有一个文件
    #     return 1
    #
    # def edittorrenttracker(self, thash, origin, new):
    #     info = self.get_url('/api/v2/torrents/editTracker?hash=' + thash +
    #                         '&origUrl=' + origin + '&newUrl=' + new)
    #     self.logger.debug('status code = ' + str(info.status_code))
    #     if info.status_code == 200:
    #         return True
    #     elif info.status_code == 400:
    #         self.logger.error('newUrl is not a valid URL')
    #     elif info.status_code == 404:
    #         self.logger.error('Torrent hash was not found')
    #     elif info.status_code == 409:
    #         self.logger.error('newUrl already exists for the torrent or origUrl was not found')
    #     return False

    def checktorrenttracker(self, thash):
        trackers = self.qbapi.torrentTrackers(thash)
        for val in trackers:
            if val.find('https') != 0 and val.find('http') == 0:
                new = val[:4] + 's' + val[4:]
                self.qbapi.editTracker(thash, val, new)
                self.logger.info('更新tracker的http为https')

    # def get_url(self, url):
    #     """Return BeautifulSoup Pages
    #     :url: page url
    #     :returns: BeautifulSoups
    #     """
    #     # self.logger.debug('Get url: ' + url)
    #     trytime = 3
    #     while trytime > 0:
    #         try:
    #             req = self._session.get(self._root + url, timeout=(5, 30))
    #             return req
    #         except BaseException as e:
    #             self.logger.debug(e)
    #             trytime -= 1
    #             time.sleep(5)
    #
    # def post_url(self, url, data=None, files=None):
    #     """Return BeautifulSoup Pages
    #     :url: page url
    #     :returns: BeautifulSoups
    #     """
    #     # self.logger.debug('Get url: ' + url)
    #     trytime = 3
    #     while trytime > 0:
    #         try:
    #             req = self._session.post(self._root + url, files=files, data=data, timeout=(5, 30))
    #             return req
    #         except BaseException as e:
    #             self.logger.debug(e)
    #             trytime -= 1
    #             time.sleep(5)

    def addtorrent(self, content, thash, page):
        # 判断种子是否存在
        if not self.istorrentexist(thash):

            # 如果是新种或者服务器无返回结果，或者查询失败，则直接下载
            if page.createtimestamp > 1800:
                inquery = self.inqueryreseed(thash)
                if self.addpassivereseed(thash, inquery, content, page):
                    return True

            # 下载分配空间
            if not self.checksize(page.size):
                return

            if self.qbapi.addNewTorrentByBin(content, pause=False, category=self.maincategory, autoTMM=True):
                self.logger.info('addreseed successfully info hash = ' + thash)
                # 添加辅种功能后不再等待，否则经常在此等待
                # 防止磁盘卡死,当磁盘碎片太多或磁盘负载重时此处会卡几到几十分钟
                # while not self.gettorrentdlstatus(thash):
                #     time.sleep(5)

                # 删除匹配的tracker,暂时每个种子都判断不管是哪个站点
                self.removematchtracker(thash, 'pttrackertju.tjupt.org')

                self.checktorrenttracker(thash)
                # self.qbapi.resumeTorrents(thash)
                with open(self.rechecklistname, 'a', encoding='UTF-8')as f:
                    f.write(self.config['name'] + ',' + page.id + ',' + 'dl' + ',' + thash + ',' + str(
                        page.futherstamp) + ',' + 'f' + '\n')
                return True
            return False
        else:
            self.logger.warning('torrent already exist hash=' + thash)
            #  若种子已存在，是否在下载目录、辅种目录、其他目录
            #  如果在下载目录，则已经为主，不动作
            #  如果在辅种目录，看主在哪个目录，若在下载目录，则换分类，若在辅种目录，报错！若在其他目录，则不动作
            #  如果在其他目录，则已经为主，不动作
            self.inctpriority(thash, self.maincategory)
            return True

    # 返回单位大小为Byte
    def getdirsize(self, tdir):
        size = 0
        if os.path.isdir(tdir):
            for root, dirs, files in os.walk(tdir):
                size += sum([getsize('\\\\?\\' + join(root, name)) for name in files])
        elif os.path.isfile(tdir):
            size += getsize(tdir)
        elif os.path.isfile(tdir + '.!qB'):
            size += getsize(tdir + '.!qB')
        return size

    def getdiskleftsize(self, diskletter):
        p = psutil.disk_usage(diskletter + ':\\')[2] / 1024 / 1024 / 1024
        # self.logger.info(self.diskletter + '盘剩余空间' + str(p) + 'GB')
        return p

    def checktorrentdtanddd(self, thash):
        ret = True
        if not self.istorrentdlcom(thash):
            ret = False
            self.deletetorrent(thash)
        return ret

    def removematchtracker(self, thash, trackerstr):
        trackerlist = self.qbapi.torrentTrackers(thash)
        for val in trackerlist:
            if trackerstr in val:
                self.qbapi.removeTrackers(thash, val)

    # def removetorrenttracker(self, thash, url):
    #     info = self.get_url('/api/v2/torrents/removeTrackers?hash=' + thash + '&urls=' + url)
    #     if info.status_code == 200:
    #         self.logger.debug('remove tracker successfully')
    #         return True
    #     elif info.status_code == 409:
    #         self.logger.error('All urls were not found')
    #     elif info.status_code == 404:
    #         self.logger.error('Torrent hash was not found')
    #     else:
    #         self.logger.error('Unknow error')
    #     return True

    def sortfilterwithreseed(self, tlist, method):
        temptlist = []
        with open(self.reseedjsonname, 'r', encoding='UTF-8') as f:
            jsonlist = json.loads(f.read())
            for val in tlist:
                if val['hash'] in jsonlist:
                    rsinfolist = jsonlist[val['hash']]['rslist']
                    isincommonct = True
                    rss = {}
                    for rs in rsinfolist:
                        rsca = self.qbapi.torrentInfo(rs['hash'])
                        if len(rsca) == 0 or not (
                                rsca['category'] in self.dlcategory or rsca['category'] == self.reseedcategory):
                            isincommonct = False
                            break
                        rss[rs['hash']] = rsca
                    if isincommonct:
                        sumtime = val[method]
                        i = 1
                        rslisthash = []
                        for rs in rsinfolist:
                            if rs['hash'] in rss:
                                rslisthash.append(rs['hash'])
                                if method == 'last_activity' and rss[rs['hash']][method] > time.time():  # 没有活动过不能计算进去
                                    continue
                                sumtime += rss[rs['hash']][method]
                                i += 1
                        avergetime = sumtime / i
                        val[method] = avergetime
                        val['reseedlist'] = rslisthash
                        temptlist.append(val)
                else:
                    val['reseedlist'] = []
                    temptlist.append(val)
            if method == 'added_on':
                temptlist.sort(key=lambda x: x['added_on'])
            elif method == 'last_activity':
                temptlist.sort(key=lambda x: x['last_activity'])
        return temptlist

    # def gettorrentinfo(self, thash):
    #     listjs = {}
    #     info = self.get_url('/api/v2/torrents/info?hashes=' + thash)
    #     self.logger.debug('get torrent info status code = ' + str(info.status_code))
    #     if info.status_code == 200:
    #         listjs = info.json()
    #         if len(listjs) == 0:
    #             return []
    #         return listjs[0]
    #     return []

    #  若种子已存在，是否在下载目录、辅种目录、其他目录
    #  如果在下载目录，则已经为主，不动作
    #  如果在辅种目录，看主在哪个目录，若在下载目录，则转换并文件链接，若在辅种目录，报错！若在其他目录，则不动作
    #  如果在其他目录，则已经为主，不动作
    def inctpriority(self, thash, category):
        jsonlist = {}
        rsca = self.qbapi.torrentInfo(thash)
        # 若种子已存在辅种目录
        if rsca['category'] == self.reseedcategory:
            # 在则检查主辅，
            with open(self.reseedjsonname, 'r', encoding='UTF-8') as f:
                jsonlist = json.loads(f.read())
            # 这里应该为辅，如果没有人为操作
            if not thash in jsonlist:
                hasfound = False
                temp = None
                for k, v in jsonlist.items():
                    for idx, val in enumerate(v['rslist']):
                        if val['hash'] == thash:
                            hasfound = True
                            temp = (k, idx)
                            break
                # 应该能找到，不能找到则有问题
                if hasfound:
                    # 若有主，主是否在下载目录，如果是，则转换，如果不是，则此种子已经为辅，不必换
                    rsca = self.qbapi.torrentInfo(temp[0])
                    if rsca['category'] in self.dlcategory or rsca['category'] == self.reseedcategory:
                        # 如果是，则转换
                        listinfo = jsonlist[temp[0]]
                        del jsonlist[temp[0]]
                        origininfo = listinfo['info']
                        origininfo['status'] = 1
                        rslist = listinfo['rslist']
                        newinfo = {}
                        newinfo['info'] = rslist[temp[1]]
                        del rslist[temp[1]]
                        rslist.append(origininfo)
                        del newinfo['info']['status']
                        newinfo['rslist'] = rslist
                        jsonlist[thash] = newinfo
                        with open(self.reseedjsonname, 'w', encoding='UTF-8') as f:
                            f.write(json.dumps(jsonlist))
                        # 由于各种种子活动状态的不确定性，容易导致移动文件卡死，大文件跨分区的话还容易浪费硬盘性能，目前解决方案为换分类不换目录
                        sec_rsca = self.qbapi.torrentInfo(thash)
                        # TODO
                        self.changerstcategory(rsca, sec_rsca, rtcategory=category)
                else:
                    self.logger.error('没找找到种子，出问题了')
                    exit(6)
            else:
                self.logger.error('疑似人为操作,程序退出！')
                exit(5)
        elif rsca['category'] in self.dlcategory:
            self.logger.debug('此种子已在下载目录！')
        else:
            self.logger.debug('此种子已在其他目录！')

    def createhardfiles(self, srcpath, srcname, content, dst, hash, name):

        dst = dst + hash
        # if os.path.exists(dst+hash):
        #     return
        if len(content) == 0:
            self.logger.error('路径为空，创建失败')
        # 判断\\防止目录+单文件形式
        if len(content) == 1 and (not '\\' in content[0]['name']):
            os.makedirs('\\\\?\\' + dst, exist_ok=True)
            try:
                os.link('\\\\?\\' + srcpath + content[0]['name'], '\\\\?\\' + dst + '\\' + name)
            except FileExistsError as e:
                self.logger.warning(e)
            except FileNotFoundError as e:
                self.logger.warning('链接失败，尝试使用后缀.!qB链接')
                try:
                    os.link('\\\\?\\' + srcpath + content[0]['name'] + '.!qB', '\\\\?\\' + dst + '\\' + name)
                except FileExistsError as _e:
                    self.logger.error(_e)
        else:
            dst = dst + '\\' + name
            srcnamelen = len(srcname)
            # os.makedirs(dst, exist_ok=True)
            for val in content:
                dirname, basename = os.path.split(val['name'])
                os.makedirs('\\\\?\\' + dst + dirname[srcnamelen:], exist_ok=True)
                try:
                    os.link('\\\\?\\' + srcpath + val['name'], '\\\\?\\' + dst + dirname[srcnamelen:] + '\\' + basename)
                except FileExistsError as e:
                    self.logger.warning(e)
                except FileNotFoundError as e:
                    self.logger.warning('链接失败，尝试使用后缀.!qB链接')
                    try:
                        os.link('\\\\?\\' + srcpath + val['name'] + '.!qB',
                                '\\\\?\\' + dst + dirname[srcnamelen:] + '\\' + basename)
                    except FileExistsError as _e:
                        self.logger.error(_e)
        return True
                # for root, dirs, files in os.walk(srcpath + srcname):
            #     # print(root, dirs, files)
            #     for dir in dirs:
            #         relativepath = root[srcpathlo + len(srcname):]
            #         os.makedirs(dst + relativepath + '\\' + dir, exist_ok=True)
            #     for file in files:
            #         relativepath = root[srcpathlo + len(srcname):]
            #         # 这里报错有可能是路径名过长
            #         os.link(root + '\\' + file, dst + relativepath + '\\' + file)

    def changerstcategory(self, ptinfo, rtinfo, rtstationname=None, rtcategory=None):
        # 由于各种种子活动状态的不确定性，容易导致移动文件卡死，大文件跨分区的话还容易浪费硬盘性能，目前解决方案为换分类不换目录
        # mainpath = self.dlcategory[self.maincategory]['savePath']
        self.qbapi.setAutoManagement([ptinfo['hash'], rtinfo['hash']], False)
        # self.qbapi.setAutoManagement(rtinfo['hash'], False)
        # self.changetorrentsavepath(ptinfo['hash'],mainpath+'Reseed')
        # Reseed的时候主目录是 ---TEST ok
        if rtstationname is not None:
            self.qbapi.setTorrentsCategory(rtinfo['hash'], gl.get_value('config')[rtstationname]['maincategory'])
        elif rtcategory is not None:
            self.qbapi.setTorrentsCategory(rtinfo['hash'], rtcategory)
        self.qbapi.setTorrentsCategory(ptinfo['hash'], self.reseedcategory)

    def post_ressed(self, thash):
        """Return BeautifulSoup Pages
        :url: page url
        :returns: BeautifulSoups
        """
        # self.logger.debug('Get url: ' + url)
        hashstr = ''
        if isinstance(thash, str):
            hashstr = '["' + thash + '"]'
        elif isinstance(thash, list):
            hashstr += '['
            for val in thash:
                hashstr += '"' + val + '",'
            hashstr = hashstr[:-1]
            hashstr += ']'
        data = {
            "hash": hashstr,
            "version": "0.2.0",
            "timestamp": time.time(),
            "sign": gl.get_value('config').token
        }
        trytime = 3
        while trytime > 0:
            try:
                req = self._session.post('http://pt.iyuu.cn/api/infohash', data=data, timeout=(10, 30))
                return req
            except BaseException as e:
                self.logger.debug(e)
                trytime -= 1
                time.sleep(5)

    def inqueryreseed(self, thash):
        info = self.post_ressed(thash)
        res = []
        if info.status_code == 200:
            self.logger.debug(info.text)
            if info.text != 'null':

                retmsg = {}
                try:
                    retmsg = json.loads(info.text)
                except:
                    self.logger.error('解析json字符串失败，请联系开发者')
                if 'success' in retmsg and retmsg['success']:
                    self.logger.error('未知错误。返回信息为）' + info.text)
                elif 'success' in retmsg and (not retmsg['success']):
                    self.logger.error('查询返回失败，错误信息' + retmsg['errmsg'])
                elif len(retmsg) != 0:
                    for val in retmsg[thash]['torrent']:
                        # 跳过自己的种
                        if val['info_hash'] == thash:
                            continue
                        if supportsid(val['sid']):
                            res.append({
                                'sid': val['sid'],
                                'tid': val['torrent_id'],
                                'hash': val['info_hash']
                            })
            else:
                self.logger.debug('服务器返回null，未查询到辅种数据')
        else:
            self.logger.error('请求服务器失败！错误状态码:' + str(info.status_code))
        return res

    # 添加被辅种时，查看有没有
    def addpassivereseed(self, thash, rsinfos, content, page):
        if len(rsinfos) == 0:
            return False
        case = 0
        comlist = [val for val in rsinfos if self.istorrentdlcom(val['hash'])]  # 用来检测种子是否被下载并完成
        if len(comlist) == 0:
            return False
        #  未做 要判断已经辅种失败的种子，就直接下载把，不要辅种了，这种概率很低，可以忽略 未做
        othercatecount = [0, []]
        dlcatecount = [0, []]
        rscatecount = [0, []]
        for val in comlist:
            ct = self.gettorrentcategory(val['hash'])
            if ct in self.dlcategory:
                dlcatecount[0] += 1
                dlcatecount[1].append(val)
            elif ct == self.reseedcategory:
                rscatecount[0] += 1
                rscatecount[1].append(val)
            else:
                othercatecount[0] += 1
                othercatecount[1].append(val)
                break
        ptinfo = None
        if othercatecount[0] > 0:
            ptinfo = othercatecount[1][0]
        elif dlcatecount[0] > 0:
            ptinfo = dlcatecount[1][0]
        else:
            # 讲道理不会运行这里的
            self.logger.warning('运行到奇怪的地方了，赶紧看看是为什么')
            ptinfo = rscatecount[1][0]

        ptinfo = self.qbapi.torrentInfo(ptinfo['hash'])
        dircontent = self.qbapi.torrentFiles(ptinfo['hash'])
        # 防止ReSeed目录里嵌套ReSeed目录
        filterdstpath = ptinfo['save_path']
        filelist = ptinfo['save_path'].split('\\')
        if len(filelist) >= 3:
            pos = 0
            if filelist[-1] == 'ReSeed':
                pos = -1
            elif filelist[-2] == 'ReSeed':
                pos = -2
            elif filelist[-3] == 'ReSeed':
                pos = -3
            if pos != 0:
                filterdstpath = ''
                for i in range(0, len(filelist) + pos):
                    filterdstpath += filelist[i] + '\\'
        self.createhardfiles(ptinfo['save_path'], ptinfo['name'], dircontent, filterdstpath + 'ReSeed\\',
                             thash[:6],
                             get_torrent_name(content))

        if self.qbapi.addNewTorrentByBin(content, pause=True, category=self.reseedcategory, autoTMM=False,
                                         savepath=filterdstpath + 'ReSeed' + '\\' + thash[:6]):
            self.logger.info('addtorrent  successfully info hash = ' + thash)

            while not self.gettorrentdlstatus(thash):
                time.sleep(5)

            # 删除匹配的tracker,暂时每个种子都判断不管是哪个站点
            self.removematchtracker(thash, 'pttrackertju.tjupt.org')

            self.checktorrenttracker(thash)
            change = 'f'
            if othercatecount[0] > 0:
                change = 'f'
            elif dlcatecount[0] > 0:
                change = 't'
            else:
                change = 'f'
            with open(self.rechecklistname, 'a', encoding='UTF-8')as f:
                f.write(self.config['name'] + ','
                        + page.id + ','
                        + 'rs' + ','
                        + thash + ','
                        + str(page.futherstamp) + ','
                        + change + ','
                        + ptinfo['hash'] + '\n')
            return True
        return False

    def addreseed(self, prhash, rsinfo, content):

        ptinfo = self.qbapi.torrentInfo(prhash)
        dircontent = self.qbapi.torrentFiles(prhash)

        # 防止ReSeed目录里嵌套ReSeed目录
        filterdstpath = ptinfo['save_path']
        filelist = ptinfo['save_path'].split('\\')
        if len(filelist) >= 3:
            pos = 0
            if filelist[-1] == 'ReSeed':
                pos = -1
            elif filelist[-2] == 'ReSeed':
                pos = -2
            elif filelist[-3] == 'ReSeed':
                pos = -3
            if pos != 0:
                filterdstpath = ''
                for i in range(0, len(filelist) + pos):
                    filterdstpath += filelist[i] + '\\'
        if not self.createhardfiles(ptinfo['save_path'], ptinfo['name'], dircontent, filterdstpath + 'ReSeed\\',
                             rsinfo['hash'][:6],
                             get_torrent_name(content)):
            return False

        if self.qbapi.addNewTorrentByBin(content, pause=True, category=self.reseedcategory, autoTMM=False,
                                         savepath=filterdstpath + 'ReSeed' + '\\' + rsinfo['hash'][:6]):
            self.logger.info('addreseed successfully info hash = ' + rsinfo['hash'])

            # 辅种不需要等待，因为文件本来就存在不需要分配空间
            # 防止磁盘卡死,当磁盘碎片太多或磁盘负载重时此处会卡几到几十分钟
            # while not self.gettorrentdlstatus(rsinfo['hash']):
            #     time.sleep(5)

            # 删除匹配的tracker,暂时每个种子都判断不管是哪个站点
            self.removematchtracker(rsinfo['hash'], 'pttrackertju.tjupt.org')

            self.checktorrenttracker(rsinfo['hash'])
            with open(self.rechecklistname, 'a', encoding='UTF-8')as f:
                f.write(getsidname(rsinfo['sid']) + ','
                        + str(rsinfo['tid']) + ','
                        + 'rs' + ','
                        + rsinfo['hash'] + ','
                        + str(time.time()) + ','
                        + 'f,'
                        + prhash + '\n')
            return True
        return False

    def recheck(self):
        dellist = []
        self.recheckreport.init()
        if os.path.exists(self.rechecklistname):
            allline = []
            with open(self.rechecklistname, 'r', encoding='UTF-8') as f:
                for line in f.readlines():
                    allline.append(line)
            for line in allline:
                self.recheckreport.listlen += 1
                rct = line.strip().split(',')
                if self.rechecktorrent(rct):
                    dellist.append(line)
        newstr = ''
        updatefile = False
        self.logger.info(self.recheckreport)
        if len(dellist) != 0 and os.path.exists(self.rechecklistname):
            with open(self.rechecklistname, 'r', encoding='UTF-8') as f:
                for line in f.readlines():
                    if line in dellist:
                        updatefile = True
                    else:
                        newstr += line
        if updatefile:
            with open(self.rechecklistname, 'w', encoding='UTF-8') as f:
                f.write(newstr)

    def rechecktorrent(self, rct):
        # 下载种子看是否下载完毕
        if rct[2] == 'dl':
            self.recheckreport.dllen += 1
            if self.istorrentexist(rct[3]):
                if self.istorrentdlcom(rct[3]):
                    self.recheckreport.dlcom += 1
                    # testOK
                    inquery = self.inqueryreseed(rct[3])
                    if self.addactivereseed(rct[0], rct[1], rct[3], inquery):
                        return True
                    return True
                else:
                    self.recheckreport.dling += 1
                    return self.checkdltorrenttime(rct)
            else:
                self.recheckreport.dlmiss += 1
                # 种子不见了，可以删掉了
                return True
        # 辅种种子，看是否校验成功
        elif rct[2] == 'rs':
            self.recheckreport.rslen += 1
            if self.istorrentexist(rct[3]):
                res = self.istorrentcheckcom(rct[3])
                if res == 0:
                    # 辅种失败
                    # testOK
                    self.recheckreport.jyfail += 1
                    self.deletetorrent(rct[3], True)
                    self.addfailrttopritlist(rct[0], rct[1], rct[3], rct[6])
                    return True
                elif res == 1:
                    # 还未检查完毕
                    # testOK
                    self.recheckreport.jying += 1
                    return False
                elif res == 2:
                    # 是否要交换主从顺序
                    self.recheckreport.jysucc += 1
                    if rct[5] == 't':
                        # testok
                        self.inctpriority2(rct[3], rct[0], rct[1], rct[6])
                    else:
                        # testOK
                        self.addrstopritlist(rct[0], rct[1], rct[3], rct[6])
                    self.qbapi.resumeTorrents(rct[3])
                    return True
                elif res == -1:
                    self.logger.warning('返回值为-1，未知错误')
                    return False
            else:
                # 种子不见了，可以删掉了
                self.recheckreport.rsmiss += 1
                return True
        else:
            self.logger.warning('Unknow type')
        return False

    def inctpriority2(self, rehash, rsname, rstid, prihash):
        jsonlist = {}
        # 在则检查主辅，
        with open(self.reseedjsonname, 'r', encoding='UTF-8') as f:
            jsonlist = json.loads(f.read())

        temp = None
        if prihash in jsonlist:
            for idx, val in enumerate(jsonlist[prihash]['rslist']):
                if val['hash'] == rehash:
                    # 正常应该找不到，因为这是新种子，辅种信息里没有这个种子的
                    temp = idx
                    break

            # 若有主，主是否在下载目录，如果是，则转换，如果不是，则此种子已经为辅，不必换
            rsca = self.qbapi.torrentInfo(prihash)
            if rsca['category'] in self.dlcategory or rsca['category'] == self.reseedcategory:
                # 如果是，则转换
                if temp is not None:
                    # 不应该有这个新种的辅种信息
                    self.logger.warning('此处不应该有新种的辅种信息')
                    listinfo = jsonlist[prihash]
                    del jsonlist[prihash]
                    origininfo = listinfo['info']
                    origininfo['status'] = 1
                    rslist = listinfo['rslist']
                    newinfo = {}
                    newinfo['info'] = rslist[temp]
                    del rslist[temp]
                    rslist.append(origininfo)
                    del newinfo['info']['status']
                    newinfo['rslist'] = rslist
                    jsonlist[rehash] = newinfo
                else:
                    listinfo = jsonlist[prihash]
                    del jsonlist[prihash]
                    origininfo = listinfo['info']
                    origininfo['status'] = 1
                    rslist = listinfo['rslist']
                    newinfo = {}
                    newinfo['info'] = {
                        'hash': rehash,
                        'tid': int(rstid) if isinstance(rstid, str) else rstid,
                        'sname': rsname
                    }
                    rslist.append(origininfo)
                    newinfo['rslist'] = rslist
                    jsonlist[rehash] = newinfo
                with open(self.reseedjsonname, 'w', encoding='UTF-8') as f:
                    f.write(json.dumps(jsonlist))
                # 由于各种种子活动状态的不确定性，容易导致移动文件卡死，大文件跨分区的话还容易浪费硬盘性能，目前解决方案为换分类不换目录
                sec_rsca = self.qbapi.torrentInfo(rehash)
                self.changerstcategory(rsca, sec_rsca, rtstationname=rsname)
        else:
            rsca = self.qbapi.torrentInfo(prihash)
            jsonlist[rehash] = {
                'info': {
                    'hash': rehash,
                    # 'sid': getnamesid(prname),
                    'tid': int(rstid) if isinstance(rstid, str) else rstid,
                    'sname': rsname
                },
                'rslist': [{
                    'hash': prihash,
                    # 'sid': getnamesid(prname),
                    'tid': 0,
                    'sname': '',
                    'status': 1
                }]
            }
            with open(self.reseedjsonname, 'w', encoding='UTF-8') as f:
                f.write(json.dumps(jsonlist))
            # 由于各种种子活动状态的不确定性，容易导致移动文件卡死，大文件跨分区的话还容易浪费硬盘性能，目前解决方案为换分类不换目录
            sec_rsca = self.qbapi.torrentInfo(rehash)
            self.changerstcategory(rsca, sec_rsca, rtstationname=rsname)

    def addactivereseed(self, prname, prid, prhash, inquery):
        # 如果在辅种目录说明前面重新辅种了这个种子，从下载状态变换到辅种状态了，跳过即可
        if self.qbapi.torrentInfo(prhash)['category'] == self.reseedcategory:
            return
        jsonlist = {}
        if os.path.exists(self.reseedjsonname):
            with open(self.reseedjsonname, 'r', encoding='UTF-8') as f:
                jsonlist = json.loads(f.read())
        if prhash in jsonlist:
            self.logger.error('不应该存在这个种子主种信息')
        else:
            jsonlist[prhash] = {
                'info': {
                    'hash': prhash,
                    # 'sid': getnamesid(prname),
                    'tid': int(prid) if isinstance(prid, str) else prid,
                    'sname': prname
                },
                'rslist': []
            }
        with open(self.reseedjsonname, 'w', encoding='UTF-8') as f:
            f.write(json.dumps(jsonlist))
        for val in inquery:
            if getsidname(val['sid']).lower() in self.stationref:
                # 先判断种子在不在，有可能多个站点相同的新种差不多一起下载完，那么把其他站点相同的删掉，变成辅种
                # 正常来说这个种子是不在的，因为下载 前进行过辅种检查，新种才会有这种情况
                # TODO ----test
                if self.istorrentexist(val['hash']):
                    self.logger.warning('辅种种子竟然存在，转为辅种策略.检查看这两个种子是否为新种子' + val['hash'])
                    self.recheckall_judge(prhash, val)
                else:
                    rspstream, rspres = self.stationref[getsidname(val['sid']).lower()].getdownloadbypsk(
                        str(val['tid']))
                    if rspres:
                        self.addreseed(prhash, val, rspstream.content)
                    else:
                        self.logger.warning('种子下载失败，可能被删除了.' + val['hash'])

    def addrstopritlist(self, rsname, rsid, rshash, prhash):
        if os.path.exists(self.reseedjsonname):
            jsonlist = ''
            with open(self.reseedjsonname, 'r', encoding='UTF-8') as f:
                jsonlist = json.loads(f.read())
            if prhash in jsonlist:
                rslist = jsonlist[prhash]['rslist']
                isex = False
                isexidx = -1
                for idx, val in enumerate(rslist):
                    if val['hash'] == rshash:
                        isex = True
                        isexidx = idx
                        break
                if isex:
                    self.logger.warning('代码跑到奇怪的地方了，这里不应该有这个种子的辅种信息')
                    jsonlist[prhash]['rslist'][isexidx] = {
                        'hash': rshash,
                        'tid': int(rsid) if isinstance(rsid, str) else rsid,
                        'sname': rsname,
                        # 'sid': getnamesid(rsname),
                        'status': 2
                    }
                else:
                    # 添加辅种信息到主种
                    rsinfo = {
                        'hash': rshash,
                        'tid': int(rsid) if isinstance(rsid, str) else rsid,
                        'sname': rsname,
                        # 'sid': getnamesid(rsname),
                        'status': 1
                    }
                    rslist.append(rsinfo)
                with open(self.reseedjsonname, 'w', encoding='UTF-8') as f:
                    f.write(json.dumps(jsonlist))
            else:
                self.logger.warning('json里没有主种信息')
                jsonlist[prhash] = {
                    'info': {
                        'hash': prhash,
                        # 'sid': getnamesid(prname),
                        'tid': 0,
                        'sname': ''
                    },
                    'rslist': [{
                        'hash': rshash,
                        # 'sid': getnamesid(prname),
                        'tid': int(rsid) if isinstance(rsid, str) else rsid,
                        'sname': rsname,
                        'status': 1
                    }]
                }
                with open(self.reseedjsonname, 'w', encoding='UTF-8') as f:
                    f.write(json.dumps(jsonlist))
        else:
            # 辅种不应该不存在文件
            self.logger.error('添加辅种信息怎么可能没有文件呢')

    def addfailrttopritlist(self, rsname, rsid, rshash, prhash):
        if os.path.exists(self.reseedjsonname):
            jsonlist = ''
            with open(self.reseedjsonname, 'r', encoding='UTF-8') as f:
                jsonlist = json.loads(f.read())
            if prhash in jsonlist:
                rslist = jsonlist[prhash]['rslist']
                isex = False
                isexidx = -1
                for idx, val in enumerate(rslist):
                    if val['hash'] == rshash:
                        isex = True
                        isexidx = idx
                        break
                if isex:
                    self.logger.warning('代码跑到奇怪的地方了，这里不应该有这个种子的辅种信息')
                    jsonlist[prhash]['rslist'][isexidx] = {
                        'hash': rshash,
                        'tid': int(rsid) if isinstance(rsid, str) else rsid,
                        'sname': rsname,
                        # 'sid': getnamesid(rsname),
                        'status': 2
                    }
                else:
                    # 添加辅种信息到主种
                    rsinfo = {
                        'hash': rshash,
                        'tid': int(rsid) if isinstance(rsid, str) else rsid,
                        'sname': rsname,
                        # 'sid': getnamesid(rsname),
                        'status': 2
                    }
                    rslist.append(rsinfo)
                with open(self.reseedjsonname, 'w', encoding='UTF-8') as f:
                    f.write(json.dumps(jsonlist))
            else:
                self.logger.warning('json里没有主种信息')
                jsonlist[prhash] = {
                    'info': {
                        'hash': prhash,
                        # 'sid': getnamesid(prname),
                        'tid': 0,
                        'sname': ''
                    },
                    'rslist': [{
                        'hash': rshash,
                        # 'sid': getnamesid(prname),
                        'tid': int(rsid) if isinstance(rsid, str) else rsid,
                        'sname': rsname,
                        'status': 2
                    }]
                }
                with open(self.reseedjsonname, 'w', encoding='UTF-8') as f:
                    f.write(json.dumps(jsonlist))
        else:
            # 辅种不应该不存在文件
            self.logger.error('添加辅种信息怎么可能没有文件呢')

    def recheckall(self):
        reseedlist = {}
        reseedalllist = []
        self.recheckallreport.init()
        if os.path.exists(self.reseedjsonname):
            with open(self.reseedjsonname, 'r', encoding='UTF-8')as f:
                reseedlist = json.loads(f.read())
        for key, value in reseedlist.items():
            reseedalllist.append(key)
            for val in value['rslist']:
                reseedalllist.append(val['hash'])
        qblist = self.qbapi.torrentsInfo(filter='completed')
        for val in qblist:
            if val['category'] == 'Reseed':  # 不收集辅种分类，否则可能会导致在辅种中再辅种的问题
                continue
            if not val['hash'] in reseedalllist:
                reseedlist[val['hash']] = {
                    'info': {
                        'hash': val['hash'],
                        'tid': 0,
                        'sanme': ''
                    },
                    'rslist': []
                }
        # 提取全部主种的hash
        prialllist = []
        for key, value in reseedlist.items():
            prialllist.append(key)

        reslist = self.inqueryreseeds(prialllist)
        self.logger.info('可辅种大小：' + str(len(reslist)))
        self.recheckallreport.listlen = len(prialllist)

        for key, value in reslist.items():
            self.logger.info('检查主种.' + key)
            if len(value['torrent']) == 0:
                self.recheckallreport.nofznum += 1
            for val in value['torrent']:
                self.recheckallreport.rsnum += 1
                self.logger.info('检查辅种' + val['hash'] + ',tid:' + str(val['tid']) + ',sid:' + str(val['sid']))
                if val['hash'] in reseedalllist:
                    self.recheckallreport.yfznum += 1
                    continue
                if self.istorrentexist(val['hash']):
                    self.recheckallreport.fzingnum += 1
                    if not self.istorrentdlcom(val['hash']):
                        self.recheckall_judge(key, val)
                else:
                    self.recheckallreport.newfznum += 1
                    rspstream, rspres = self.stationref[getsidname(val['sid'])].getdownloadbypsk(str(val['tid']))
                    if rspres:
                        # 种子下载有问题的时候name空的，有一定几率会误判种子下载成功了，和网络状况有关
                        if get_torrent_name(rspstream.content) is None:
                            self.recheckallreport.failnum += 1
                            continue
                        self.recheckallreport.succnum += 1
                        self.addreseed(key, val, rspstream.content)
                    else:
                        self.recheckallreport.failnum += 1
                        self.logger.warning('种子下载失败，可能被删除了.' + val['hash'])
        self.logger.info(self.recheckallreport)

    def inqueryreseeds(self, thashs):
        info = self.post_ressed(thashs)
        res = {}
        if info is None:
            self.logger.error('连接辅种服务器失败')
            return {}
        if info.status_code == 200:
            # self.logger.debug(info.text)
            if info.text != 'null':

                retmsg = {}
                try:
                    retmsg = json.loads(info.text)
                except:
                    self.logger.error('解析json字符串失败，请联系开发者')
                if 'success' in retmsg and retmsg['success']:
                    self.logger.error('未知错误。返回信息为）' + info.text)
                elif 'success' in retmsg and (not retmsg['success']):
                    self.logger.error('查询返回失败，错误信息' + retmsg['errmsg'])
                elif len(retmsg) != 0:
                    for key, value in retmsg.items():
                        res[key] = {'torrent': []}
                        for idx, val in enumerate(value['torrent']):
                            if not supportsid(val['sid']):
                                continue
                            if val['info_hash'] == key:
                                continue
                            res[key]['torrent'].append({
                                'hash': val['info_hash'],
                                'tid': val['torrent_id'],
                                'sid': val['sid']
                            })
            else:
                self.logger.debug('服务器返回null，未查询到辅种数据')
        else:
            self.logger.error('请求服务器失败！错误状态码:' + str(info.status_code))
        return res

    def recheckall_judge(self, prihash, rsinfo):
        thash = rsinfo['hash']
        newstr = ''
        updatefile = False
        if os.path.exists(self.rechecklistname):
            with open(self.rechecklistname, 'r', encoding='UTF-8') as f:
                for line in f.readlines():
                    rct = line.strip().split(',')
                    if rct[3] == thash and rct[1] == 'dl':
                        self.deletetorrent(thash, True)
                        updatefile = True
                    else:
                        newstr += line
        if updatefile:
            with open(self.rechecklistname, 'w', encoding='UTF-8') as f:
                f.write(newstr)
            # 在if里，只有dl情况，并且没有下载完才需要删除并辅种，校验中的不应该进入这里
            # 在recheck里，可能会存在多站点相同新种同时下载完毕，导致互相辅种创建硬链接浪费空间，用这个函数重新辅种
            rspstream, rspres = self.stationref[getsidname(rsinfo['sid'])].getdownloadbypsk(rsinfo['tid'])
            if rspres:
                self.addreseed(prihash, rsinfo, rspstream.content)
            else:
                self.logger.warning('种子下载失败，可能被删除了.' + rsinfo['hash'])

    def checkdltorrenttime(self, dline):
        ret = False
        if float(dline[4]) > 0:
            if float(dline[4]) - time.time() > 1800:
                ret = False
            else:
                self.deletetorrent(dline[3])
                self.logger.info(dline[0] + ':删除' + dline[3] + ',' + dline[1] + '因为没有在免费时间内下载完毕')
                ret = True
        return ret
