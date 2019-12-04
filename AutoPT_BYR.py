"""
Byr
自动从bt.byr.cn上下载免费种子文件，保存到指定位置
Author: LYS
Create: 2019年11月13日
"""
import os
import pickle
import time
from io import BytesIO
from urllib.parse import unquote
from urllib.parse import urlparse, parse_qs

import requests
from PIL import Image
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

import QBmana
import TorrentHash
import globalvar as gl
from AutoPT import AutoPT, AutoPT_Page


class AutoPT_BYR(AutoPT):
    """login/logout/getpage"""

    def __init__(self):
        super(AutoPT_BYR, self).__init__('BYR')

    @property
    def pages(self):
        """Return pages in torrents.php
        :returns: yield ByrPage pages
        """
        # free url
        self.logger.debug('Get pages')
        filterclass = ''
        filterurl = ''
        if self.config['checkptmode'] == 1:
            filterurl = 'torrents.php?'
            filterclass = 'free_bg'
        elif self.config['checkptmode'] == 2:
            filterurl = 'torrents.php?spstate=2'
            filterclass = 'free_bg'
        page = self.get_url(filterurl)
        n = 0
        try:
            # 防止网页获取失败时的异常
            for line in page.find_all('tr', class_=filterclass) or page.find_all('tr', class_='twoupfree_bg'):
                if n == 0:
                    yield (AutoPT_Page(line))
                    n = 1
                else:
                    n -= 1
        except BaseException as e:
            self.logger.error(e)


class AutoPT_Page_BYR(AutoPT_Page):
    """Torrent Page Info"""

    def __init__(self, soup):
        """Init variables
        :soup: Soup
        """
        AutoPT_Page.__init__(self, soup)

    @property
    def ok(self):
        """Check torrent info
        :returns: If a torrent are ok to be downloaded
        """
        return self.size < 2048
