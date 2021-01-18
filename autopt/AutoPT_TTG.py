import json
import time
import traceback
from random import randint
from urllib.parse import parse_qs, urlparse

import demjson
from bs4 import BeautifulSoup

import tools.globalvar as gl
from autopt import AutoPT


class AutoPT_TTG(AutoPT.AutoPT):
    """login/logout/getpage"""

    def __init__(self):
        super(AutoPT_TTG, self).__init__('TTG')
        self.autoptpage = AutoPT_Page_TTG

    def login(self):
        try:
            # image_file.show()
            # captcha_text = input('If image can not open in your system, then open the url below in browser\n'
            #                     + self._root + image_url + '\n' + 'Input Code:')
            self.app.getlogindata(self.stationname)

            # 取消登录，强制退出
            if not gl.get_value('logindata')[0]:
                exit('取消登录')

            login_data = {
                'username': gl.get_value('logindata')[1]['username'],
                'password': gl.get_value('logindata')[1]['password'],
                # 'otp': gl.get_value('logindata')[1]['secondverify'],
                'passan': '',
                'passid': '0',
                'lang': '0',
                # 'rememberme': 'yes',

            }
            main_page = self._session.post(
                self._root + 'takelogin.php', login_data, headers=self.headers, timeout=(30, 30))
            if main_page.status_code == 200 and main_page.url == self._root + '2fa.php':
                page = BeautifulSoup(main_page.text, 'lxml')
                authcode = page.select('input[name=authenticity_token]')
                if len(authcode) == 0:
                    return False
                authcode = authcode[0].attrs['value']
                uid = page.select('input[name=uid]')
                if len(uid) == 0:
                    return False
                uid = uid[0].attrs['value']
                login_data = {
                    'authenticity_token': authcode,
                    'uid': uid,
                    'otp': gl.get_value('logindata')[1]['secondverify'],
                }
                main_page = self._session.post(
                    self._root + 'take2fa.php', login_data, headers=self.headers, timeout=(30, 30))
            if main_page.url != self._root + 'my.php':
                self.logger.error('Login error')
                return False
            self._save()
        except BaseException as e:
            self.logger.exception(traceback.format_exc())
            exit(4)
            return False
        return True

    def judgetorrentok(self, page):
        if page.method == 0:
            if page.futherstamp != -1:
                return (page.futherstamp - time.time() > 5 * 60 * 60) and page.seeders < 2
            else:
                return page.seeders < 2
        elif page.method == 1:
            if page.futherstamp != -1:
                return (page.futherstamp - time.time() > 5 * 60 * 60) and page.seeders < 3
            else:
                return page.seeders < 3

    def attendance(self, page):
        try:
            if len(page.find_all('a', id='signed')) != 0:
                for signcode in page.find_all('script', {'type': 'text/javascript'}):
                    for line in str(signcode).split('\n'):
                        if 'signed.php' in line:
                            line = line[line.find('{'):line.find('}') + 1]
                            postdata = demjson.decode(line)
                            info = self._session.post(self._root + 'signed.php', postdata, timeout=(30, 30))
                            self.logger.info(info.text.encode('ISO-8859-1').decode('utf-8'))
                            return True
        except BaseException as e:
            self.logger.error('签到失败,发生异常')
            self.logger.debug(e)
        return False

    @property
    def pages(self):
        """Return pages in torrents.php
        :returns: yield ByrPage pages
        """
        # free url
        self.logger.debug('Get Media pages')
        filterurl = 'browse.php?c=M'
        page = self.get_url(filterurl)
        self.logger.debug('Get pages Done')

        # 自动签到
        self.attendance(page)

        # 监测二次验证导致的登录问题
        recheckpage = False
        n = 1
        try:
            # 防止网页获取失败时的异常
            for line in page.find('table', id='torrent_table').find_all('tr'):
                # print(line)
                # print('\n\n\n\n\n')
                if n == 0:
                    recheckpage = True
                    if line.find('img', src='/pic/ico_2xfree.gif') is not None and \
                            line.find('img', src='/pic/hit_run.gif') is None and not self.config['onlyattendance']:
                        yield self.autoptpage(line, 1)
                    elif line.find('img', src='/pic/ico_free.gif') is not None and \
                            line.find('img', src='/pic/hit_run.gif') is None and not self.config['onlyattendance']:
                        yield self.autoptpage(line)
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

        self.logger.debug('Get Game&Ware pages')
        filterurl = 'browse.php?c=G'
        page = self.get_url(filterurl)
        self.logger.debug('Get pages Done')
        # 监测二次验证导致的登录问题
        recheckpage = False
        n = 1
        try:
            # 防止网页获取失败时的异常
            for line in page.find('table', id='torrent_table').find_all('tr'):
                # print(line)
                # print('\n\n\n\n\n')
                if n == 0:
                    recheckpage = True
                    if line.find('img', src='/pic/ico_2xfree.gif') is not None and \
                            line.find('img', src='/pic/hit_run.gif') is None and not self.config['onlyattendance']:
                        yield self.autoptpage(line, 1)
                    elif line.find('img', src='/pic/ico_free.gif') is not None and \
                            line.find('img', src='/pic/hit_run.gif') is None and not self.config['onlyattendance']:
                        yield self.autoptpage(line)
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
                return BeautifulSoup(req.text.encode('ISO-8859-1').decode('utf-8'), 'lxml')
            except BaseException as e:
                self.logger.debug(e)
                trytime -= 1
                time.sleep(3)

    def getdownload(self, id_):
        """Download torrent in url
        :url: url
        :filename: torrent filename
        """
        url = self._root + 'dl/' + id_ + '/' + str(randint(500, 10000))
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
        url = self._root + 'dl/' + id_ + '/' + self.psk
        trytime = 0
        req = None

        while trytime < 3:
            try:
                req = self._session.get(url, timeout=(30, 60))

                if req.status_code == 200:
                    # 第二个返回值为这种子是否还存在的标志，提供的是接口
                    return req, True
                elif req.status_code == 404:
                    # 该种子不存在
                    return req, False
                else:
                    trytime += 1
                    self.logger.error('Download Fail trytime = ' + str(trytime))
                    time.sleep(10)
            except BaseException as e:
                self.logger.error('Download Fail trytime = ' + str(trytime))
                trytime += 1
                # self.logger.exception(traceback.format_exc())
                self.logger.debug(e)
        return req, False


class AutoPT_Page_TTG(AutoPT.AutoPT_Page):
    """Torrent Page Info"""

    def __init__(self, soup, method=0):
        """Init variables
        :soup: Soup
        """
        self.logger = gl.get_value('logger').logger
        self.method = method
        self.url = soup.find(class_='name_left').a['href']
        self.name = soup.find(class_='name_left').find('img', class_='report')['torrentname']
        self.id = soup.find(class_='name_left').find('img', class_='report')['torrent']
        self.type = soup.find('td').find('img')['alt']
        self.createtime = soup.find_all('td')[-6].text
        self.createtimestamp = time.mktime(time.strptime(self.createtime, "%Y-%m-%d%H:%M:%S"))
        self.size = self.tosize(soup.find_all('td')[-4].text)
        self.seeders = int(soup.find_all('td')[-2].text.split('/')[0])
        self.leechers = int(soup.find_all('td')[-2].text.split('\n')[-1])
        self.snatched = int(soup.find_all('td')[-3].text.replace('次', '').replace(',', ''))
        self.lefttime = ''
        self.futherstamp = -1
        try:
            # 注意，字符串中间这个不是空格
            # if self.name.endswith('[email protected]'):
            #     self.name = self.name[:len('[email protected]') * -1]
            lefttimetext = None
            for span in soup.find(class_='name_left').find_all('span'):
                if '剩余' in span.text:
                    lefttimetext = str(span).split('到')[1].split(',')[0]
                    break
            if lefttimetext is not None:
                self.lefttime = lefttimetext
                self.futherstamp = time.mktime(time.strptime(self.lefttime, "%Y年%m月%d日%H点%M分"))

        except BaseException as e:
            # 没有限制时间
            self.lefttime = ''
            self.futherstamp = -1

    @property
    def ok(self):
        """Check torrent info
        :returns: If a torrent are ok to be downloaded
        """
        self.logger.info(
            self.id + ',' + self.name + ',' + self.type + ',' + self.createtime + ',' + str(self.size) + 'GB,' + str(
                self.seeders) + ',' + str(self.leechers) + ',' + str(self.snatched) + ',' + str(self.lefttime))
        if self.method == 0:
            return self.size < 512 and self.seeders > 0
        elif self.method == 1:
            return self.size < 1024 and self.seeders > 0
