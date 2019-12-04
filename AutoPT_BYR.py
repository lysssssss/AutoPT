"""
Byr
自动从bt.byr.cn上下载免费种子文件，保存到指定位置
Author: LYS
Create: 2019年11月13日
"""

from AutoPT import AutoPT, AutoPT_Page


class AutoPT_BYR(AutoPT):
    """login/logout/getpage"""

    def __init__(self):
        super(AutoPT_BYR, self).__init__('BYR')
        self.autoptpage = AutoPT_Page_BYR

    def judgetorrentok(self, page):
        return True


class AutoPT_Page_BYR(AutoPT_Page):
    """Torrent Page Info"""

    def __init__(self, soup):
        """Init variables
        :soup: Soup
        """
        AutoPT_Page.__init__(self, soup)
