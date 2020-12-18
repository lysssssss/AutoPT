import time
import traceback
from io import BytesIO
from urllib.parse import parse_qs, urlparse

from PIL import Image
from bs4 import BeautifulSoup

import tools.globalvar as gl
from autopt import AutoPT


class AutoPT_LEMONHD(AutoPT.AutoPT):
    """login/logout/getpage"""

    def __init__(self):
        super(AutoPT_LEMONHD, self).__init__('LEMONHD')
        self.autoptpage = AutoPT_Page_LEMONHD

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
                'steptwocode': gl.get_value('logindata')[1]['secondverify']
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
        if page.method == 0:
            if page.futherstamp != -1:
                return (page.futherstamp - time.time() > 22 * 60 * 60) and page.seeders < 3
            else:
                return page.seeders < 3
        elif page.method == 1:
            if page.futherstamp != -1:
                return (page.futherstamp - time.time() > 22 * 60 * 60) and page.seeders < 5
            else:
                return page.seeders < 5

    def attendance(self, page):
        try:
            if page.find('a', href='attendance.php') is not None:
                self.logger.info('尝试签到...')
                info = self.get_url('attendance.php')
                for line in info.find_all('td', class_='text'):
                    if '本次签到' in str(line):
                        self.logger.info(line.text)
                        return True
                self.logger.error('签到失败,未知原因')
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
        self.logger.debug('Get pages')
        filterurl = 'torrents_new.php'
        page = self.get_url(filterurl)
        self.logger.debug('Get pages Done')

        # 自动签到
        self.attendance(page)

        # 监测二次验证导致的登录问题
        recheckpage = False
        n = 1
        try:
            # 防止网页获取失败时的异常
            for line in page.find('table', class_='torrents').find_all('tr'):
                if n == 0:
                    if not gl.get_value('thread_flag'):
                        return
                    recheckpage = True
                    if line.find('img', class_='pro_free2up') is not None and \
                            line.find('img', class_='hitandrun') is None and not self.config['onlyattendance']:
                        yield self.autoptpage(line, 1)
                        n = 1
                    elif line.find('img', class_='pro_free') is not None and \
                            line.find('img', class_='hitandrun') is None and not self.config['onlyattendance']:
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


class AutoPT_Page_LEMONHD(AutoPT.AutoPT_Page):
    """Torrent Page Info"""

    def __init__(self, soup, method=0):
        """Init variables
        :soup: Soup
        """
        try:
            self.logger = gl.get_value('logger').logger
            self.method = method
            url = soup.find(class_='torrentname').a['href']
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
            self.id = parse_qs(urlparse(url).query)['id'][0]
            self.futherstamp = -1
            self.lefttime = [tmp_span.text for tmp_span
                             in soup.find(class_='torrentname').find_all('span')
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
        if self.method == 0:
            return self.size < 128 and 0 < self.seeders
        elif self.method == 1:
            return self.size < 256 and 0 < self.seeders
