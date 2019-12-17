import datetime
import time
import traceback

from bs4 import BeautifulSoup

import globalvar as gl
from AutoPT import AutoPT, AutoPT_Page


class AutoPT_TJU(AutoPT):
    """login/logout/getpage"""

    def __init__(self):
        super(AutoPT_TJU, self).__init__('TJU')
        self.autoptpage = AutoPT_Page_TJU

    def login(self):
        try:
            self.app.getlogindata(self.stationname)
            # 取消登录，强制退出
            if not gl.get_value('logindata')[0]:
                exit('取消登录')

            login_data = {
                'username': gl.get_value('logindata')[1]['username'],
                'password': gl.get_value('logindata')[1]['password'],
                'logout': 'forever',
            }
            main_page = self._session.post(
                self._root + 'takelogin.php', login_data)
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
            if page.size < 16:
                return (page.futherstamp - time.time() > 24 * 60 * 60) and page.seeders < 5
            else:
                return page.ipv6 == 'conn-yes' and (page.futherstamp - time.time() > 24 * 60 * 60) and page.seeders < 5
        else:
            if page.size < 16:
                return page.seeders < 5
            else:
                return page.ipv6 == 'conn-yes' and page.seeders < 5


class AutoPT_Page_TJU(AutoPT_Page):
    """Torrent Page Info"""

    def __init__(self, soup):
        """Init variables
        :soup: Soup
        """
        super(AutoPT_Page_TJU, self).__init__(soup)
        try:
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
        # conn conn-yes
        # conn conn--
        # conn conn-no
        self.school4 = soup.find(id='school4')['class'][1]
        self.ipv6 = soup.find(id='ipv6')['class'][1]
        self.public4 = soup.find(id='public4')['class'][1]
        pass

    @property
    def ok(self):
        """Check torrent info
        :returns: If a torrent are ok to be downloaded
        """
        self.logger.info(self.id + ',' + self.name + ',' + self.type + ',' + str(self.size) + 'GB,' + str(
            self.seeders) + ',' + str(self.leechers) + ',' + str(self.snatched) + ',' + str(self.lefttime))
        # 判断self.seeders > 0 因为没人做种时无法知道此种子的连接性如何, 等待有人做种
        return self.size < 256 and self.seeders > 0
