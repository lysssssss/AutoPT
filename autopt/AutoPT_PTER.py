import time
import traceback
from io import BytesIO

from PIL import Image
from bs4 import BeautifulSoup

import tools.globalvar as gl
from autopt import AutoPT


class AutoPT_PTER(AutoPT.AutoPT):
    """login/logout/getpage"""

    def __init__(self):
        super(AutoPT_PTER, self).__init__('PTER')
        self.autoptpage = AutoPT_Page_PTER

    def login(self):
        try:
            login_page = self.get_url('login.php')
            image_url = login_page.find('img', alt='CAPTCHA')['src']
            image_hash = login_page.find(
                'input', attrs={'name': 'imagehash'})['value']
            self.logger.info('Image url: ' + image_url)
            self.logger.info('Image hash: ' + image_hash)
            req = self._session.get(self._root + image_url, timeout=(30, 30))
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
                'imagehash': image_hash,
                'verify_code': gl.get_value('logindata')[1]['secondverify']
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

    def judgetorrentok(self, page):
        if page.futherstamp != -1:
            return (page.futherstamp - time.time() > 5 * 60 * 60) and page.seeders < 13
        else:
            return page.seeders < 13

    def attendance(self, page):
        try:
            if page.find('a', id='do-attendance') is not None:
                self.logger.info('尝试签到...')
                info = self._session.get(self._root + 'attendance-ajax.php', timeout=(30, 30))
                if info.json()['status'] == '1':
                    self.logger.info(info.json()['data'])
                    self.logger.info(info.json()['message'])
                    self.logger.info('签到成功')
                else:
                    self.logger.warning(info.json()['data'])
                    self.logger.warning(info.json()['message'])
                    self.logger.error('签到失败')
        except BaseException as e:
            self.logger.error('签到失败')
            self.logger.exception(traceback.format_exc())

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

        # 自动签到
        self.attendance(page)

        # 监测二次验证导致的登录问题
        recheckpage = False
        n = 0
        try:
            # 防止网页获取失败时的异常
            for line in page.find_all('tr', class_='sticky_top'):
                if n == 0:
                    if not gl.get_value('thread_flag'):
                        return
                    recheckpage = True
                    yield self.autoptpage(line)
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
            for line in page.find_all('tr', class_='sticky_normal'):
                if n == 0:
                    if not gl.get_value('thread_flag'):
                        return
                    recheckpage = True
                    yield self.autoptpage(line)
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
            for line in page.find_all('tr', class_='twoupfree_bg'):
                if n == 0:
                    if not gl.get_value('thread_flag'):
                        return
                    recheckpage = True
                    yield self.autoptpage(line)
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
                    yield self.autoptpage(line)
                    n = 1
                else:
                    n -= 1
        except BaseException as e:
            self.logger.exception(traceback.format_exc())
        if not recheckpage:
            self.logger.warning('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!界面没有找到种子标签!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')


class AutoPT_Page_PTER(AutoPT.AutoPT_Page):
    """Torrent Page Info"""

    def __init__(self, soup):
        """Init variables
        :soup: Soup
        """
        super(AutoPT_Page_PTER, self).__init__(soup)
        try:
            # 注意，字符串中间这个不是空格
            if self.name.endswith('[email protected]'):
                self.name = self.name[:len('[email protected]') * -1]
            self.lefttime = [tmp_span.text for tmp_span
                             in BeautifulSoup(str(soup.find(class_='torrentname')), 'lxml').find_all('span')
                             if self.matchlefttimestr(tmp_span.text)]
            if len(self.lefttime) == 1:
                self.lefttime = self.lefttime[0]
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
        self.logger.info(
            self.id + ',' + self.name + ',' + self.type + ',' + self.createtime + ',' + str(self.size) + 'GB,' + str(
                self.seeders) + ',' + str(self.leechers) + ',' + str(self.snatched) + ',' + str(self.lefttime))
        return self.size < 128
