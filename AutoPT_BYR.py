"""
Byr
自动从bt.byr.cn上下载免费种子文件，保存到指定位置
Author: LYS
Create: 2019年11月13日
"""
import os
import pickle
import random
import time
from io import BytesIO
from urllib.parse import unquote
from urllib.parse import urlparse, parse_qs

import requests
from PIL import Image
from bs4 import BeautifulSoup

import QBmana
import TorrentHash
import globalvar as gl


class Byr(object):
    """login/logout/getpage"""

    def __init__(self):
        """Byr Init """
        self.config = gl.get_value('config')['BYR']
        self.logger = gl.get_value('logger').logger
        self.app = gl.get_value('wxpython')

        self._session = requests.session()
        self._session.headers = {
            'User-Agent': 'Mozilla/5.0 AppleWebKit/537.36 Chrome/79.0.3945.16 Safari/537.36 Edg/79.0.309.11'
        }

        self._root = 'https://bt.byr.cn/'
        self.list = []
        self.qbapi = QBmana.QBAPI(self.config)
        if os.path.exists('list.csv'):
            self.logger.debug('Read list.csv')
            with open('list.csv', 'r', encoding='UTF-8') as f:
                for line in f.readlines():
                    self.list.append(line.split(',')[0])
        self.logger.info('初始化成功，开始监听')

    def random_agent(self):
        user_agent_list = [
            "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/68.0.3440.106 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/67.0.3396.99 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/64.0.3282.186 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36",
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/45.0.2454.101 Safari/537.36",
            "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)",
            "Mozilla/5.0 (Macintosh; U; PPC Mac OS X 10.5; en-US; rv:1.9.2.15) Gecko/20110303 Firefox/3.6.15",
            "Mozilla/5.0 AppleWebKit/537.36 Chrome/79.0.3945.16 Safari/537.36 Edg/79.0.309.11"
        ]
        str = random.choice(user_agent_list)
        self.logger.debug(str)
        self._session.headers = {
            'User-Agent': str
        }

    def login(self):
        """Login to bt.byr.cn"""
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
        #                      + self._root + image_url + '\n' + 'Input Code:')
        self.app.getlogindata('BYR', image_file)

        # 取消登录，强制退出
        if not gl.get_value('logindata')[3]:
            exit(4)

        self.logger.debug('Captcha text: ' + gl.get_value('logindata')[2])

        login_data = {
            'username': gl.get_value('logindata')[0],
            'password': gl.get_value('logindata')[1],
            'imagestring': gl.get_value('logindata')[2],
            'imagehash': image_hash
        }
        main_page = self._session.post(
            self._root + 'takelogin.php', login_data)
        if main_page.url != self._root + 'index.php':
            self.logger.error('Login error')
            return
        self._save()

    def _save(self):
        """Save cookies to file"""
        self.logger.debug('Save cookies')
        with open('cookie', 'wb') as f:
            pickle.dump(self._session.cookies, f)

    def _load(self):
        """Load cookies from file"""
        if os.path.exists('cookie'):
            with open('cookie', 'rb') as f:
                self.logger.debug('Load cookies from file.')
                self._session.cookies = pickle.load(f)
        else:
            self.logger.debug('Load cookies by login')
            self.login()
            #self._save()

    @property
    def pages(self):
        """Return pages in torrents.php
        :returns: yield ByrPage pages
        """
        # free url
        self.logger.debug('Get pages')
        filterclass = ''
        filterurl = ''
        if self.config.checkptmode == 1:
            filterurl = 'torrents.php?'
            filterclass = 'free_bg'
        elif self.config.checkptmode == 2:
            filterurl = 'torrents.php?spstate=2'
            filterclass = 'free_bg'
        page = self.get_url(filterurl)
        n = 0
        try:
            # 防止网页获取失败时的异常
            for line in page.find_all('tr', class_=filterclass) or page.find_all('tr', class_='twoupfree_bg'):
                if n == 0:
                    yield (ByrPage(line))
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

    def start(self):
        """Start spider"""
        self.logger.debug('Start Spider')
        self._load()
        with open('list.csv', 'a', encoding='UTF-8') as f:
            try:
                for page in self.pages:
                    self.logger.debug(page.id + ',' + page.name + ',' + page.type + ',' + str(page.size) + 'GB,' + str(
                        page.seeders) + ',' + str(page.snatched))
                    if page.id not in self.list and page.ok:
                        self.logger.info('Download ' + page.name)
                        req_dl = self.getdownload(page.id)
                        thash = TorrentHash.get_torrent_hahs40(req_dl.content) if req_dl.status_code == 200 else ''

                        if self.config.autoflag:
                            # check disk capaciry
                            if req_dl.status_code == 200:
                                self.qbapi.addtorrent(req_dl.content, thash, page.size)
                                f.write(page.id + ',' + page.name + ',' + str(page.size) + 'GB,'
                                        + str(page.seeders) + ','
                                        + str(thash) + '\n')
                                self.list.append(page.id)
                                # 防反爬虫
                                time.sleep(3)

                            else:
                                self.logger.error('Download Error:' + page.id + ',' + page.name + ','
                                                  + page.type + ',' + str(page.size) + 'GB,'
                                                  + str(page.seeders) + ',' + str(page.snatched))
                        else:
                            if req_dl.status_code == 200:
                                filename = req_dl.headers['content-disposition']
                                filename = unquote(filename[filename.find('name') + 5:])
                                with open(self.config.dlroot + filename, 'wb') as fp:
                                    fp.write(req_dl.content)
                                self.list.append(page.id)
                                f.write(
                                    page.id + ',' + page.name + ',' + str(page.size) + 'GB,' + str(page.seeders) + ','
                                    + str(thash) + '\n')
                                # 防反爬虫
                                time.sleep(3)
                            else:
                                self.logger.error('Download Error:' + page.id + ',' + page.name + ','
                                                  + page.type + ',' + str(page.size) + 'GB,'
                                                  + str(page.seeders) + ',' + str(page.snatched))
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
                filename = req.headers['content-disposition']
                filename = unquote(filename[filename.find('name') + 5:])
                # with open(self.config.dlroot + filename, 'wb') as f:
                # f.write(req.content)
                break
            else:
                req = self._session.get(url)
                trytime += 1
                self.logger.error('Download Fail trytime = ' + str(trytime))
                time.sleep(10)
        return req


class ByrPage(object):
    """Torrent Page Info"""

    def __init__(self, soup):
        """Init variables
        :soup: Soup
        """

        url = soup.find(class_='torrentname').a['href']
        self.name = soup.find(class_='torrentname').b.text
        self.type = soup.img['title']
        self.size = self.tosize(soup.find_all('td')[-5].text)
        self.seeders = int(soup.find_all('td')[-4].text.replace(',', ''))
        self.snatched = int(soup.find_all('td')[-2].text.replace(',', ''))
        self.id = parse_qs(urlparse(url).query)['id'][0]

    @property
    def ok(self):
        """Check torrent info
        :returns: If a torrent are ok to be downloaded
        """
        return self.size < 2048

    def tosize(self, text):
        """Convert text 'xxxGB' to int size
        :text: 123GB or 123MB
        :returns: 123(GB) or 0.123(GB)
        """
        if text.endswith('MB'):
            size = float(text[:-2].replace(',', '')) / 1024
        elif text.endswith('TB'):
            size = float(text[:-2].replace(',', '')) * 1024
        else:
            size = float(text[:-2].replace(',', ''))
        return size
