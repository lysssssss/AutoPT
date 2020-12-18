import datetime
import os
import pickle
import time
import traceback
from abc import abstractmethod, ABC
from io import BytesIO
from urllib.parse import urlparse, parse_qs

import cloudscraper
from PIL import Image
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

import tools.globalvar as gl
from autopt import QBmanage_Reseed
from tools import TorrentInfo


class AutoPT(ABC):
    """login/logout/getpage"""

    def __init__(self, stationname):
        basepath = 'autopt/'
        self.stationname = stationname.upper()
        self.config = gl.get_value('config')[self.stationname]
        self.logger = gl.get_value('logger').logger
        self.app = gl.get_value('wxpython')

        self._session = cloudscraper.create_scraper(delay=5)
        self.csvfilename = basepath + 'torrentslist/' + self.stationname + '_list.csv'
        self.webagentfilename = basepath + 'useragent/' + self.stationname + '_webagent'
        self.cookiefilename = basepath + 'cookies/' + self.stationname + '_cookie'
        self._root = self.config['root']
        self.psk = self.config['passkey']
        self.list = []
        self.autoptpage = AutoPT_Page
        self.manager = QBmanage_Reseed.Manager(self.config)
        self.useragent = ''
        self.readwebagent()
        self.headers = {
            'User-Agent': self.useragent
        }
        if self.config['switch']:
            self._load()
        if os.path.exists(self.csvfilename):
            self.logger.debug('Read list.csv')
            with open(self.csvfilename, 'r', encoding='UTF-8') as f:
                for line in f.readlines():
                    self.list.append(line.split(',')[0])
        # self.logger.info('初始化成功，开始监听')

    def login(self):
        try:
            login_page = self.get_url('login.php')
            image_url = login_page.find('img', alt='CAPTCHA')['src']
            image_hash = login_page.find(
                'input', attrs={'name': 'imagehash'})['value']
            self.logger.info('Image url: ' + image_url)
            self.logger.info('Image hash: ' + image_hash)
            req = self._session.get(self._root + image_url, headers=self.headers, timeout=(30, 30))
            image_file = Image.open(BytesIO(req.content))
            # image_file.show()
            # captcha_text = input('If image can not open in your system, then open the url below in browser\n'
            #                     + self._root + image_url + '\n' + 'Input Code:')
            self.app.getlogindata(self.stationname, image_file)

            # 取消登录，强制退出
            if not gl.get_value('logindata')[0]:
                exit('取消登录')

            self.logger.debug('Captcha text: ' + gl.get_value('logindata')[1]['captcha'])

            login_data = {
                'username': gl.get_value('logindata')[1]['username'],
                'password': gl.get_value('logindata')[1]['password'],
                'imagestring': gl.get_value('logindata')[1]['captcha'],
                'imagehash': image_hash
            }
            main_page = self._session.post(
                self._root + 'takelogin.php', login_data, headers=self.headers, timeout=(30, 30))
            if main_page.url != self._root + 'index.php':
                self.logger.error('Login error')
                return False
            self._save()
        except BaseException as e:
            self.logger.exception(traceback.format_exc())
            exit(4)
            return False
        return True

    def _save(self):
        """Save cookies to file"""
        self.logger.debug('Save cookies')
        with open(self.cookiefilename, 'wb') as f:
            pickle.dump(self._session.cookies, f)

    def _load(self):
        """Load cookies from file"""
        while not os.path.exists(self.cookiefilename):
            self.logger.debug('Load cookies by login')
            self.login()
            # self._save()
        with open(self.cookiefilename, 'rb') as f:
            self.logger.debug('Load cookies from file.')
            self._session.cookies = pickle.load(f)

    @property
    def pages(self):
        """Return pages in torrents.php
        :returns: yield ByrPage pages
        """
        # free url
        self.logger.debug('Get pages')
        filterurl = 'torrents.php?'
        page = self.get_url(filterurl)
        self.logger.debug('Get pages Done')

        # 监测二次验证导致的登录问题
        recheckpage = False
        n = 0
        try:
            # 防止网页获取失败时的异常
            for line in page.find_all('tr', class_='twoupfree_bg'):
                if n == 0:
                    if not gl.get_value('thread_flag'):
                        return
                    recheckpage = True
                    if not self.config['onlyattendance']:
                        yield self.autoptpage(line, 1)
                    n = 1
                else:
                    n -= 1
        except BaseException as e:
            self.logger.exception(traceback.format_exc())

        if not gl.get_value('thread_flag'):
            return

        n = 0
        try:
            # 防止网页获取失败时的异常
            for line in page.find_all('tr', class_='free_bg'):
                if n == 0:
                    if not gl.get_value('thread_flag'):
                        return
                    recheckpage = True
                    if not self.config['onlyattendance']:
                        yield self.autoptpage(line)
                    n = 1
                else:
                    n -= 1
        except BaseException as e:
            self.logger.exception(traceback.format_exc())
        if not recheckpage:
            self.logger.warning('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!界面没有找到种子标签!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            if self.config['onlyattendance']:
                self.logger.warning('仅签到失败')

    def get_url(self, url):
        """Return BeautifulSoup Pages
        :url: page url
        :returns: BeautifulSoups
        """
        # self.logger.debug('Get url: ' + url)
        trytime = 3
        while trytime > 0:
            try:
                req = self._session.get(self._root + url, headers=self.headers, timeout=(10, 60))
                self.logger.debug('获取页面状态' + str(req.status_code))
                return BeautifulSoup(req.text, 'lxml')
            except BaseException as e:
                self.logger.debug(e)
                trytime -= 1
                time.sleep(3)

    def pageinfotocsv(self, f, page):
        f.write(page.id + ',' + page.name + ',' + str(page.size) + 'GB,' + page.lefttime + '\n')

    # 纯虚函数,子类必须实现软条件
    @abstractmethod
    def judgetorrentok(self, page):
        pass

    def start(self):
        """Start spider"""
        self.logger.info('Start Spider [' + self.stationname + ']')
        if self.config['onlyattendance']:
            self.logger.info('仅签到模式')
        # self.checktorrenttime()
        # self._load()
        with open(self.csvfilename, 'a', encoding='UTF-8') as f:
            try:
                for page in self.pages:
                    if not gl.get_value('thread_flag'):
                        continue
                    if page.id not in self.list and page.ok:
                        # page.ok为第一次筛选，不符合条件的会再次检查
                        # 下面方法为第二次筛选，不符合条件的下次不会再检查
                        # 不符合条件的就不下载,直接添加到csv里
                        if not self.judgetorrentok(page):
                            self.pageinfotocsv(f, page)
                            self.list.append(page.id)
                            continue
                        # 通过条件后再开始下载
                        req_dl = self.getdownload(page.id)
                        thash = TorrentInfo.get_torrent_hash40(req_dl.content) if req_dl.status_code == 200 else ''

                        self.logger.info('Download ' + page.name)
                        self.downloadtorrent(f, page, req_dl, thash)
            except BaseException as e:
                self.logger.exception(traceback.format_exc())
        self.logger.info('Done')

    def downloadtorrent(self, f, page, req_dl, thash):
        try:
            # check disk capaciry
            if req_dl.status_code == 200:
                self.logger.info('Add ' + page.name)
                self.manager.addtorrent(req_dl.content, thash, page)
                self.pageinfotocsv(f, page)
                # self.recordtorrenttime(page, thash)
                self.list.append(page.id)
                # 防反爬虫
                time.sleep(3)
            else:
                self.logger.error('Download Error:')

        except BaseException as e:
            self.logger.error(e)
            # self.logger.exception(traceback.format_exc())

    def getdownload(self, id_):
        """Download torrent in url
        :url: url
        :filename: torrent filename
        """
        url = self._root + 'download.php?' + self.config['urlparam'] + 'id=' + id_
        trytime = 0
        req = None

        while trytime < 3:
            try:
                req = self._session.get(url, timeout=(30, 60))
                if req.status_code == 200:
                    break
                else:
                    trytime += 1
                    self.logger.error('Download Fail trytime = ' + str(trytime))
                    time.sleep(10)
            except BaseException as e:
                self.logger.error('Download Fail trytime = ' + str(trytime))
                trytime += 1
                # self.logger.exception(traceback.format_exc())
                self.logger.debug(e)
        return req

    def getdownloadbypsk(self, id_):
        """Download torrent in url
        :url: url
        :filename: torrent
        """
        if isinstance(id_, int):
            id_ = str(id_)
        url = self._root + 'download.php?' + self.config['urlparam'] + 'id=' + id_ + '&passkey=' + self.psk
        trytime = 0
        req = None

        while trytime < 3:
            try:
                req = self._session.get(url, timeout=(30, 60))
                #  60为b'<', 如果get出来的是html而不是种子字节流说明种子被删除了或其他原因
                if req.status_code == 200 and req.content[0] != 60:
                    # 第二个返回值为这种子是否还存在的标志，提供的是接口
                    return req, True
                elif req.status_code == 404:
                    # 该种子不存在
                    return req, False
                else:
                    trytime += 1
                    self.logger.error('Download Fail trytime = ' + str(trytime))
                    time.sleep(3)
            except BaseException as e:
                self.logger.error('Download Fail trytime = ' + str(trytime))
                trytime += 1
                # self.logger.exception(traceback.format_exc())
                self.logger.debug(e)
        return req, False

    def readwebagent(self):
        hasrecord = False
        if os.path.exists(self.webagentfilename):
            with open(self.webagentfilename, 'r', encoding='UTF-8') as f:
                for line in f.readlines():
                    if line != '':
                        self.useragent = line
                        hasrecord = True
                    break
        if not hasrecord:
            with open(self.webagentfilename, 'w', encoding='UTF-8') as f:
                tmpagent = UserAgent().random
                self.useragent = tmpagent
                f.write(tmpagent)


class AutoPT_Page(object):
    """Torrent Page Info"""

    def __init__(self, soup, method=0):
        """Init variables
        :soup: Soup
        """
        self.logger = gl.get_value('logger').logger
        self.method = method
        url = soup.find(class_='torrentname').a['href']
        self.name = soup.find(class_='torrentname').b.text
        # 注意，字符串中间这个不是空格
        if self.name.endswith('[email protected]'):
            self.name = self.name[:len('[email protected]') * -1]
        self.type = soup.img['title']
        self.createtime = soup.find_all('td')[-6].text
        self.createtimestamp = self.totimestamp(self.createtime)
        self.size = self.tosize(soup.find_all('td')[-5].text)
        self.seeders = int(soup.find_all('td')[-4].text.replace(',', ''))
        self.leechers = int(soup.find_all('td')[-3].text.replace(',', ''))
        self.snatched = int(soup.find_all('td')[-2].text.replace(',', ''))
        self.id = parse_qs(urlparse(url).query)['id'][0]
        self.futherstamp = -1
        self.lefttime = ''

    @property
    def ok(self):
        """Check torrent info
        :returns: If a torrent are ok to be downloaded
        """
        self.logger.info(self.id + ',' + self.name + ',' + self.type + ',' + self.createtime + ',' + str(
            self.size) + 'GB,' + str(self.seeders) + ',' + str(self.leechers) + ',' + str(self.snatched) + ',' + str(
            self.lefttime))
        if self.method == 0:
            return self.size < 128 and self.seeders > 0
        elif self.method == 1:
            return self.size < 256 and self.seeders > 0

    def tosize(self, text):
        """Convert text 'xxxGB' to int size
        :text: 123GB or 123MB
        :returns: 123(GB) or 0.123(GB)
        """
        size = 0
        if text.endswith('MB'):
            size = float(text[:-2].replace(',', '')) / 1024
        elif text.endswith('TB'):
            size = float(text[:-2].replace(',', '')) * 1024
        elif text.endswith('GB'):
            size = float(text[:-2].replace(',', ''))
        elif text.endswith('MiB'):
            size = float(text[:-3].replace(',', '')) / 1024
        elif text.endswith('TiB'):
            size = float(text[:-3].replace(',', '')) * 1024
        elif text.endswith('GiB'):
            size = float(text[:-3].replace(',', ''))
        else:
            self.logger.error('Error while transfer size')
            raise Exception('Error while transfer size')
        return size

    def mystrptime(self, strt):
        now = datetime.datetime.now()
        futhertime = now
        if '年' in strt:
            futhertime += datetime.timedelta(days=int(strt[:strt.find('年')]) * 365)  # 算365天，应该够一个种子下载完成
            strt = strt[strt.find('年') + 1:]
        if '月' in strt:
            futhertime += datetime.timedelta(days=int(strt[:strt.find('月')]) * 30)  # 算30天，应该够一个种子下载完成
            strt = strt[strt.find('月') + 1:]
        if '天' in strt:
            futhertime += datetime.timedelta(days=int(strt[:strt.find('天')]))
            strt = strt[strt.find('天') + 1:]
        # MT
        if '日' in strt:
            futhertime += datetime.timedelta(days=int(strt[:strt.find('日')]))
            strt = strt[strt.find('日') + 1:]
        if '时' in strt:
            futhertime += datetime.timedelta(hours=int(strt[:strt.find('时')]))
            strt = strt[strt.find('时') + 1:]
        # MT
        if '時' in strt:
            futhertime += datetime.timedelta(hours=int(strt[:strt.find('時')]))
            strt = strt[strt.find('時') + 1:]
        if '分' in strt:
            futhertime += datetime.timedelta(minutes=int(strt[:strt.find('分')]))
            strt = strt[strt.find('分') + 1:]
        if '秒' in strt:
            futhertime += datetime.timedelta(seconds=int(strt[:strt.find('秒')]))
            # strt = strt[strt.find('秒') + 1:]

        return time.mktime(futhertime.timetuple())

    def matchlefttimestr(self, strt):
        for val in ['天', '时', '分', '秒', '月', '日', '時', '年']:
            if val in strt:
                return True
        return False

    def totimestamp(self, strt):
        stamp = 0
        if '<' in strt:
            strt = strt[1:]
        if '年' in strt:
            stamp += int(strt[:strt.find('年')]) * 365 * 24 * 60 * 60
            strt = strt[strt.find('年') + 1:]
        if '月' in strt:
            stamp += int(strt[:strt.find('月')]) * 30 * 24 * 60 * 60
            strt = strt[strt.find('月') + 1:]
        if '天' in strt:
            stamp += int(strt[:strt.find('天')]) * 24 * 60 * 60
            strt = strt[strt.find('天') + 1:]
        # MT
        if '日' in strt:
            stamp += int(strt[:strt.find('日')]) * 24 * 60 * 60
            strt = strt[strt.find('日') + 1:]
        if '时' in strt:
            stamp += int(strt[:strt.find('时')]) * 60 * 60
            strt = strt[strt.find('时') + 1:]
        # MT
        if '時' in strt:
            stamp += int(strt[:strt.find('時')]) * 60 * 60
            strt = strt[strt.find('時') + 1:]
        if '分' in strt:
            stamp += int(strt[:strt.find('分')]) * 60
            strt = strt[strt.find('分') + 1:]
        if '秒' in strt:
            stamp += int(strt[:strt.find('秒')])
            # strt = strt[strt.find('秒') + 1:]

        return stamp
