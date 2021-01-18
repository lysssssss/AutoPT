import time
import traceback
from urllib.parse import parse_qs, urlparse

import tools.globalvar as gl
from autopt import AutoPT


class AutoPT_MTEAM(AutoPT.AutoPT):
    """login/logout/getpage"""

    def __init__(self):
        super(AutoPT_MTEAM, self).__init__('MTEAM')
        self.autoptpage = AutoPT_Page_MTEAM

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
                'User-Agent': self.useragent,
                'Referer': 'https://pt.m-team.cc/takelogin.php'

            }
            main_page = self._session.post(
                self._root + 'takelogin.php', data=login_data, headers=header, timeout=(30, 30))
            if main_page.status_code == 200 and 'verify.php' in main_page.url:
                login_data = {
                    'otp': gl.get_value('logindata')[1]['secondverify']
                }
                sec_page = self._session.post(
                    self._root + 'verify.php', login_data, headers=self.headers, timeout=(30, 30))
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
        if page.method == 0:
            if page.futherstamp != -1:
                return (page.futherstamp - time.time() > 5 * 60 * 60) and page.seeders < 1
            else:
                return page.seeders < 1
        elif page.method == 1:
            if page.futherstamp != -1:
                return (page.futherstamp - time.time() > 5 * 60 * 60) and page.seeders < 2
            else:
                return page.seeders < 2
        elif page.method == 2:
            if page.futherstamp != -1:
                return (page.futherstamp - time.time() > 5 * 60 * 60) and page.seeders < 2
            else:
                return page.seeders < 2

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
                req = self._session.get(url, headers=self.headers, timeout=(30, 60))
                if req.status_code == 200:
                    break
                else:
                    trytime += 1
                    self.logger.error('Download Fail trytime = ' + str(trytime))
                    time.sleep(10)

            except BaseException as e:
                trytime += 1
                self.logger.error('Download Fail trytime = ' + str(trytime))
                # self.logger.exception(traceback.format_exc())
                self.logger.debug(e)
        return req

    @property
    def pages(self):
        """Return pages in torrents.php
        :returns: yield ByrPage pages
        """
        # free url
        self.logger.debug('Get torrents pages')
        filterurl = 'torrents.php'
        pages = self.get_url(filterurl)
        self.logger.debug('Get torrents pages Done')
        # 监测二次验证导致的登录问题
        recheckpage = False
        n = 1
        try:
            # 防止网页获取失败时的异常
            for line in pages.find('table', class_='torrents').find_all('tr'):
                if n == 0:
                    if not gl.get_value('thread_flag'):
                        return
                    recheckpage = True
                    if line.find('img', class_='pro_free2up') is not None and not self.config['onlyattendance']:
                        yield self.autoptpage(line, 1)
                        n = 1
                    if line.find('img', class_='pro_free') is not None and not self.config['onlyattendance']:
                        yield self.autoptpage(line)
                        n = 1
                else:
                    n -= 1
        except BaseException as e:
            # self.logger.exception(traceback.format_exc())
            self.logger.debug(e)
        if not recheckpage:
            self.logger.warning('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!界面没有找到种子标签!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            if self.config['onlyattendance']:
                self.logger.warning('仅签到失败')
        elif recheckpage and self.config['onlyattendance']:
            return
        if not gl.get_value('thread_flag'):
            return

        self.logger.debug('Get adult pages')
        filterurl = 'adult.php'
        pages = self.get_url(filterurl)
        self.logger.debug('Get adult pages Done')
        # 监测二次验证导致的登录问题
        recheckpage = False
        n = 1
        try:
            # 防止网页获取失败时的异常
            for line in pages.find('table', class_='torrents').find_all('tr'):
                if n == 0:
                    if not gl.get_value('thread_flag'):
                        return
                    recheckpage = True
                    if line.find('img', class_='pro_free2up') is not None and not self.config['onlyattendance']:
                        yield self.autoptpage(line, 2)
                        n = 1
                    if line.find('img', class_='pro_free') is not None and not self.config['onlyattendance']:
                        yield self.autoptpage(line, 2)
                        n = 1
                else:
                    n -= 1
        except BaseException as e:
            # self.logger.exception(traceback.format_exc())
            self.logger.debug(e)
        if not recheckpage:
            self.logger.warning('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!界面没有找到种子标签!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            if self.config['onlyattendance']:
                self.logger.warning('仅签到失败')
        elif recheckpage and self.config['onlyattendance']:
            return
        if not gl.get_value('thread_flag'):
            return

        self.logger.debug('Get music pages')
        filterurl = 'music.php'
        pages = self.get_url(filterurl)
        self.logger.debug('Get music pages Done')
        # 监测二次验证导致的登录问题
        recheckpage = False
        n = 1
        try:
            # 防止网页获取失败时的异常
            for line in pages.find('table', class_='torrents').find_all('tr'):
                if n == 0:
                    if not gl.get_value('thread_flag'):
                        return
                    recheckpage = True
                    if line.find('img', class_='pro_free2up') is not None and not self.config['onlyattendance']:
                        yield self.autoptpage(line, 1)
                        n = 1
                    if line.find('img', class_='pro_free') is not None and not self.config['onlyattendance']:
                        yield self.autoptpage(line)
                        n = 1
                else:
                    n -= 1
        except BaseException as e:
            self.logger.debug(e)
            # self.logger.exception(traceback.format_exc())
        if not recheckpage:
            self.logger.warning('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!界面没有找到种子标签!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            if self.config['onlyattendance']:
                self.logger.warning('仅签到失败')
        elif recheckpage and self.config['onlyattendance']:
            return


class AutoPT_Page_MTEAM(AutoPT.AutoPT_Page):
    """Torrent Page Info"""

    def __init__(self, soup, method=0):
        """Init variables
        :soup: Soup
        """
        self.logger = gl.get_value('logger').logger
        self.method = method
        self.url = soup.find(class_='torrentname').a['href']
        self.name = soup.find(class_='torrentname').b.text
        # 注意，字符串中间这个不是空格
        if self.name.endswith('[email protected]'):
            self.name = self.name[:len('[email protected]') * -1]
        self.type = soup.img['title']
        self.createtime = soup.find_all('td')[-7].text
        self.createtimestamp = self.totimestamp(self.createtime)
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
                             in soup.find(class_='torrentname').find_all('span')
                             if self.matchlefttimestr(tmp_span.text)]
            if len(self.lefttime) == 1:
                self.lefttime = self.lefttime[0][3:]
                self.futherstamp = self.mystrptime(self.lefttime)
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
        self.logger.info(
            self.id + ',' + self.name + ',' + self.type + ',' + self.createtime + ','
            + str(self.size) + 'GB,' + str(self.seeders) + ',' + str(self.leechers)
            + ',' + str(self.snatched) + ',' + str(self.lefttime))
        if self.method == 0:
            return self.size < 128 and self.seeders > 0
        elif self.method == 1:
            return self.size < 256 and self.seeders > 0
        elif self.method == 2:
            return self.size < 2048 and self.seeders > 0
