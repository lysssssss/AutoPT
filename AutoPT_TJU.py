"""
Byr
自动从bt.byr.cn上下载免费种子文件，保存到指定位置
Author: LYS
Create: 2019年11月13日
"""
import datetime
import time
from urllib.parse import parse_qs, urlparse

from AutoPT import AutoPT, AutoPT_Page
import globalvar as gl

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
            self.logger.error(e)
            exit(4)
            return False
        return True


class AutoPT_Page_TJU(AutoPT_Page):
    """Torrent Page Info"""

    def __init__(self, soup):
        """Init variables
        :soup: Soup
        """
        # AutoPT_Page.__init__(self, soup)
        url = soup.find(class_='torrentname').a['href']
        self.name = soup.find(class_='torrentname').b.text
        self.now = time.time()
        try:
            self.lefttime = soup.find(class_='torrentname').span.text
            self.futherstamp = self.mystrptime(str(self.lefttime))
        except BaseException as e:
            # 没有限制时间
            self.lefttime = -1
            self.futherstamp = -1
        self.type = soup.img['title']
        self.size = self.tosize(soup.find_all('td')[-5].text)
        self.seeders = int(soup.find_all('td')[-4].text.replace(',', ''))
        self.leechers = int(soup.find_all('td')[-3].text.replace(',', ''))
        self.snatched = int(soup.find_all('td')[-2].text.replace(',', ''))
        self.id = parse_qs(urlparse(url).query)['id'][0]
        # conn conn-yes
        # conn conn--
        # conn conn-no
        self.school4 = soup.find(id='school4')['class'][1]
        self.ipv6 = soup.find(id='ipv6')['class'][1]
        self.public4 = soup.find(id='public4')['class'][1]
        pass

    def mystrptime(self, strt):
        now = datetime.datetime.now()
        futhertime = now
        if '天' in strt:
            futhertime += datetime.timedelta(days=int(strt[:strt.find('天')]))
            strt = strt[strt.find('天')+1:]
        if '时' in strt:
            futhertime += datetime.timedelta(hours=int(strt[:strt.find('时')]))
            strt = strt[strt.find('时') + 1:]
        if '分' in strt:
            futhertime += datetime.timedelta(minutes=int(strt[:strt.find('分')]))
            strt = strt[strt.find('分') + 1:]
        if '秒' in strt:
            futhertime += datetime.timedelta(seconds=int(strt[:strt.find('秒')]))
            # strt = strt[strt.find('秒') + 1:]

        return time.mktime(futhertime.timetuple())

    @property
    def ok(self):
        """Check torrent info
        :returns: If a torrent are ok to be downloaded
        """
        return self.size < 2048 and self.ipv6 == 'conn-yes'

