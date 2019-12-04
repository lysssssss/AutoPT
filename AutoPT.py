import os
import pickle
import time
from io import BytesIO
from urllib.parse import unquote
from urllib.parse import urlparse, parse_qs

import requests
from PIL import Image
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

import QBmana
import TorrentHash
import globalvar as gl


class AutoPT(object):
    """login/logout/getpage"""

    def __init__(self, stationname):
        self.stationname = stationname.upper()
        self.config = gl.get_value('config')[self.stationname]
        self.logger = gl.get_value('logger').logger
        self.app = gl.get_value('wxpython')

        self._session = requests.session()
        self._session.headers = {
            'User-Agent': UserAgent().random
        }
        self.csvfilename = self.stationname + 'list.csv'
        self.cookiefilename = self.stationname + '_cookie'
        self._root = self.config['root']
        self.list = []
        self.autoptpage = AutoPT_Page
        self.qbapi = QBmana.QBAPI(self.config)
        if os.path.exists(self.csvfilename):
            self.logger.debug('Read list.csv')
            with open(self.csvfilename, 'r', encoding='UTF-8') as f:
                for line in f.readlines():
                    self.list.append(line.split(',')[0])
        self.logger.info('初始化成功，开始监听')

    def random_agent(self):
        self._session.headers = {
            'User-Agent': UserAgent().random
        }

    def login(self):
        try:
            login_page = self.get_url('login.php')
            image_url = login_page.find('img', alt='CAPTCHA')['src']
            image_hash = login_page.find(
                'input', attrs={'name': 'imagehash'})['value']
            self.logger.info('Image url: ' + image_url)
            self.logger.info('Image hash: ' + image_hash)
            req = self._session.get(self._root + image_url)
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
                self._root + 'takelogin.php', login_data)
            if main_page.url != self._root + 'index.php':
                self.logger.error('Login error')
                return False
            self._save()
        except BaseException as e:
            self.logger.error(e)
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
        if os.path.exists(self.cookiefilename):
            with open(self.cookiefilename, 'rb') as f:
                self.logger.debug('Load cookies from file.')
                self._session.cookies = pickle.load(f)
        else:
            self.logger.debug('Load cookies by login')
            return self.login()
            # self._save()
        return True

    @property
    def pages(self):
        """Return pages in torrents.php
        :returns: yield ByrPage pages
        """
        # free url
        self.logger.debug('Get pages')
        filterclass = ''
        filterurl = ''
        if self.config['checkptmode'] == 1:
            filterurl = 'torrents.php?'
            filterclass = 'free_bg'
        elif self.config['checkptmode'] == 2:
            filterurl = 'torrents.php?spstate=2'
            filterclass = 'free_bg'
        page = self.get_url(filterurl)
        n = 0
        try:
            # 防止网页获取失败时的异常
            for line in page.find_all('tr', class_=filterclass):
                if n == 0:
                    yield (self.autoptpage(line))
                    n = 1
                else:
                    n -= 1
        except BaseException as e:
            self.logger.error(e)
        n = 0
        try:
            # 防止网页获取失败时的异常
            for line in page.find_all('tr', class_='twoupfree_bg'):
                if n == 0:
                    yield (self.autoptpage(line))
                    n = 1
                else:
                    n -= 1
        except BaseException as e:
            self.logger.error(e)

    def get_url(self, url):
        """Return BeautifulSoup Pages
        :url: page url
        :returns: BeautifulSoups
        """
        # self.logger.debug('Get url: ' + url)
        trytime = 3
        while trytime > 0:
            self.random_agent()
            try:
                req = self._session.get(self._root + url)
                return BeautifulSoup(req.text, 'lxml')
            except BaseException as e:
                self.logger.error(e)
                trytime -= 1
                time.sleep(20)

    def pageinfotocsv(self, f, page, thash):
        f.write(page.id + ',' + page.name + ',' + str(page.size) + 'GB,' + str(thash) + '\n')

    def start(self):
        """Start spider"""
        self.logger.debug('Start Spider [' + self.stationname + ']')
        self._load()
        with open(self.csvfilename, 'a', encoding='UTF-8') as f:
            try:
                for page in self.pages:
                    if page.id not in self.list and page.ok:
                        self.logger.info('Download ' + page.name)
                        req_dl = self.getdownload(page.id)
                        thash = TorrentHash.get_torrent_hash40(req_dl.content) if req_dl.status_code == 200 else ''

                        if self.config['autoflag']:
                            # check disk capaciry
                            if req_dl.status_code == 200:
                                self.logger.info('Add ' + page.name)
                                self.qbapi.addtorrent(req_dl.content, thash, page.size)
                                self.pageinfotocsv(f, page, thash)
                                self.list.append(page.id)
                                # 防反爬虫
                                time.sleep(3)

                            else:
                                self.logger.error('Download Error:')
                        else:
                            if req_dl.status_code == 200:
                                self.logger.info('Add ' + page.name)
                                filename = req_dl.headers['content-disposition']
                                filename = unquote(filename[filename.find('name') + 5:])
                                with open(self.config['dlroot'] + filename, 'wb') as fp:
                                    fp.write(req_dl.content)
                                self.list.append(page.id)
                                self.pageinfotocsv(f, page, thash)
                                # 防反爬虫
                                time.sleep(3)
                            else:
                                self.logger.error('Download Error:')
            except BaseException as e:
                self.logger.error(e)

    def getdownload(self, id_):
        """Download torrent in url
        :url: url
        :filename: torrent filename
        """
        url = self._root + 'download.php?id=' + id_
        trytime = 0
        req = self._session.get(url)
        while trytime < 6:

            if req.status_code == 200:
                # filename = req.headers['content-disposition']
                # filename = unquote(filename[filename.find('name') + 5:])
                # with open(self.config['dlroot'] + filename, 'wb') as f:
                # f.write(req.content)
                break
            else:
                req = self._session.get(url)
                trytime += 1
                self.logger.error('Download Fail trytime = ' + str(trytime))
                time.sleep(10)
        return req


class AutoPT_Page(object):
    """Torrent Page Info"""

    def __init__(self, soup):
        """Init variables
        :soup: Soup
        """
        self.logger = gl.get_value('logger').logger

        url = soup.find(class_='torrentname').a['href']
        self.name = soup.find(class_='torrentname').b.text
        self.type = soup.img['title']
        self.size = self.tosize(soup.find_all('td')[-5].text)
        self.seeders = int(soup.find_all('td')[-4].text.replace(',', ''))
        self.leechers = int(soup.find_all('td')[-3].text.replace(',', ''))
        self.snatched = int(soup.find_all('td')[-2].text.replace(',', ''))
        self.id = parse_qs(urlparse(url).query)['id'][0]

    @property
    def ok(self):
        """Check torrent info
        :returns: If a torrent are ok to be downloaded
        """
        self.logger.debug(self.id + ',' + self.name + ',' + self.type + ',' + str(self.size) + 'GB,' + str(
            self.seeders) + ',' + str(self.leechers) + ',' + str(self.snatched))
        return self.size < 2048

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
            gl.get_value('logger').logger.error('Error while transfer size')
            raise Exception('Error while transfer size')
        return size
