import hashlib
import traceback

import bencode

import tools.globalvar as gl


# import libtorrent


class Stack:
    # 模拟栈
    def __init__(self):
        self.items = []

    def isEmpty(self):
        return len(self.items) == 0

    def push(self, item):
        self.items.append(item)

    def pop(self):
        return self.items.pop()

    def peek(self):
        if not self.isEmpty():
            return self.items[len(self.items) - 1]

    def size(self):
        return len(self.items)


def get_torrent_hash40(data):
    try:
        start = data.find(b'4:info') + 6
        return hashlib.sha1(data[start:calDictEnd(data, start)]).hexdigest()
        # return str(libtorrent.torrent_info(libtorrent.bdecode(data)).info_hash())
        # mangetlink = magneturi.from_torrent_data(data)
        # mangetlink = mangetlink[mangetlink.find('btih') + 5:mangetlink.find('btih') + 5 + 32]
        # b16Hash = base64.b16encode(base64.b32decode(mangetlink))
        # b16Hash = b16Hash.lower()
        # b16Hash = str(b16Hash, "utf-8")
        # return b16Hash
    except BaseException as e:
        gl.get_value('logger').logger.exception(traceback.format_exc())


def get_torrent_name(data):
    try:
        # return str(libtorrent.torrent_info(libtorrent.bdecode(data)).name())
        metainfo = bencode.bdecode(data)

        # print (metainfo)
        return metainfo['info']['name']
    except BaseException as e:
        gl.get_value('logger').logger.exception(traceback.format_exc())


def calDictEnd(data, start):
    st = Stack()
    if data[start] == ord('d'):
        st.push(data[start])
    start += 1
    while not st.isEmpty():
        if data[start] == ord('e'):
            st.pop()
            start += 1
        elif data[start] == ord('l') or data[start] == ord('d') or data[start] == ord('i'):
            st.push(data[start])
            start += 1
        elif ord('0') <= data[start] <= ord('9'):
            num = 0
            while ord('0') <= data[start] <= ord('9'):
                num = num * 10 + (data[start] - ord('0'))
                start += 1
            if st.peek() != ord('i'):
                start += 1 + num  # 冒号加字符串长度
    return start
