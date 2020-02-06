"""
Byr
自动从bt.byr.cn上下载免费种子文件，保存到指定位置
Author: LYS
Create: 2019年11月13日
"""
import time

from autopt import AutoPT


class AutoPT_BYR(AutoPT.AutoPT):
    """login/logout/getpage"""

    def __init__(self):
        super(AutoPT_BYR, self).__init__('BYR')
        self.autoptpage = AutoPT_Page_BYR

    def judgetorrentok(self, page):
        if page.method == 0:
            if page.futherstamp != -1:
                return (page.futherstamp - time.time() > 5 * 60 * 60) and page.seeders < 10
            else:
                return page.seeders < 10
        elif page.method == 1:
            if page.futherstamp != -1:
                return (page.futherstamp - time.time() > 5 * 60 * 60) and page.seeders < 30
            else:
                return page.seeders < 30


class AutoPT_Page_BYR(AutoPT.AutoPT_Page):
    """Torrent Page Info"""

    def __init__(self, soup, method=0):
        """Init variables
        :soup: Soup
        """
        AutoPT.AutoPT_Page.__init__(self, soup, method)
