import time
import traceback
from io import BytesIO
from urllib.parse import parse_qs, urlparse

from PIL import Image
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

import globalvar as gl
from AutoPT import AutoPT, AutoPT_Page


class AutoPT_MTEAM(AutoPT):
    """login/logout/getpage"""

    def __init__(self):
        super(AutoPT_MTEAM, self).__init__('MTEAM')
        self.autoptpage = AutoPT_Page_MTEAM
        self.constagnet = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.16 Safari/537.36 Edg/80.0.361.9'
        self._session.headers = {
            'User-Agent': self.constagnet
        }

    def login(self):
        try:
            self.app.getlogindata(self.stationname)

            # 取消登录，强制退出
            if not gl.get_value('logindata')[0]:
                exit('取消登录')

            login_data = {
                'username': gl.get_value('logindata')[1]['username'],
                'password': gl.get_value('logindata')[1]['password'],
                # 'verify_code': gl.get_value('logindata')[1]['secondverify']
            }
            header = {
                'User-Agent': self.constagnet,
                'Referer': 'https://pt.m-team.cc/takelogin.php'

            }
            main_page = self._session.post(
                self._root + 'takelogin.php', data=login_data, headers=header, timeout=(30, 30))
            if main_page.status_code == 200:
                login_data = {
                    'otp': gl.get_value('logindata')[1]['secondverify']
                }
                sec_page = self._session.post(
                    self._root + 'verify.php', login_data, timeout=(30, 30))
                if sec_page.url != self._root + 'index.php':
                    self.logger.error('Login error')
                    return False
                else:
                    self._save()
                    return True
        except BaseException as e:
            self.logger.exception(traceback.format_exc())
            exit(4)
            return False
        return False

    def judgetorrentok(self, page):
        if page.futherstamp != -1:
            return (page.futherstamp - time.time() > 21 * 60 * 60) and page.seeders < 20
        else:
            return page.seeders < 20

    def getdownload(self, id_):
        """Download torrent in url
        :url: url
        :filename: torrent filename
        """
        url = self._root + 'download.php?id=' + id_ + '&ipv6=1&https=1'
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
                self.logger.exception(traceback.format_exc())
        return req

    @property
    def pages(self):
        """Return pages in torrents.php
        :returns: yield ByrPage pages
        """
        # free url
        self.logger.debug('Get torrents pages')
        filterurl = 'torrents.php'
        pages = self.get_url(filterurl, False)
        self.logger.debug('Get torrents pages Done')
        n = 1
        try:
            # 防止网页获取失败时的异常
            for line in BeautifulSoup(str(pages.find('table', class_='torrents')), 'lxml').find_all('tr'):
                if n == 0:
                    # TODO 2倍种暂时未获取
                    if line.find('img', class_='pro_free') is not None:
                        yield self.autoptpage(line)
                        n = 1
                else:
                    n -= 1
        except BaseException as e:
            self.logger.exception(traceback.format_exc())

        self.logger.debug('Get adult pages')
        filterurl = 'adult.php'
        pages = self.get_url(filterurl, False)
        self.logger.debug('Get adult pages Done')
        n = 1
        try:
            # 防止网页获取失败时的异常
            for line in BeautifulSoup(str(pages.find('table', class_='torrents')), 'lxml').find_all('tr'):
                if n == 0:
                    # TODO 2倍种暂时未获取
                    if line.find('img', class_='pro_free') is not None:
                        yield self.autoptpage(line)
                        n = 1
                else:
                    n -= 1
        except BaseException as e:
            self.logger.exception(traceback.format_exc())

        self.logger.debug('Get music pages')
        filterurl = 'music.php'
        pages = self.get_url(filterurl, False)
        self.logger.debug('Get music pages Done')
        n = 1
        try:
            # 防止网页获取失败时的异常
            for line in BeautifulSoup(str(pages.find('table', class_='torrents')), 'lxml').find_all('tr'):
                if n == 0:
                    # TODO 2倍种暂时未获取
                    if line.find('img', class_='pro_free') is not None:
                        yield self.autoptpage(line)
                        n = 1
                else:
                    n -= 1
        except BaseException as e:
            self.logger.exception(traceback.format_exc())


class AutoPT_Page_MTEAM(AutoPT_Page):
    """Torrent Page Info"""

    def __init__(self, soup):
        """Init variables
        :soup: Soup
        """
        self.logger = gl.get_value('logger').logger
        self.url = soup.find(class_='torrentname').a['href']
        self.name = soup.find(class_='torrentname').b.text
        self.type = soup.img['title']
        self.size = self.tosize(soup.find_all('td')[-6].text)
        self.seeders = int(soup.find_all('td')[-5].text.replace(',', ''))
        self.leechers = int(soup.find_all('td')[-4].text.replace(',', ''))
        self.snatched = int(soup.find_all('td')[-3].text.replace(',', ''))
        self.id = parse_qs(urlparse(self.url).query)['id'][0]
        try:
            # 注意，字符串中间这个不是空格
            if self.name.endswith('[email protected]'):
                self.name = self.name[:len('[email protected]') * -1]
            self.lefttime = [tmp_span.text for tmp_span
                             in BeautifulSoup(str(soup.find(class_='torrentname')), 'lxml').find_all('span')
                             if self.matchlefttimestr(tmp_span.text)]
            if len(self.lefttime) == 1:
                self.lefttime = self.lefttime[0][3:]
                self.futherstamp = self.mystrptime(str(self.lefttime))
            else:
                self.lefttime = ''
                self.futherstamp = -1
        except BaseException as e:
            # 没有限制时间
            self.lefttime = ''
            self.futherstamp = -1
        pass

    @property
    def ok(self):
        """Check torrent info
        :returns: If a torrent are ok to be downloaded
        """
        self.logger.info(self.id + ',' + self.name + ',' + self.type + ',' + str(self.size) + 'GB,' + str(
            self.seeders) + ',' + str(self.leechers) + ',' + str(self.snatched) + ',' + str(self.lefttime))
        return self.size < 128
