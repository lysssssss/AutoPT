import base64
import hashlib
import traceback

import bencode
import libtorrent
import magneturi

import globalvar as gl


def get_torrent_hash40(data):
    try:
        with open('ttmp.dat', 'wb') as f:
            f.write(data)
        return str(libtorrent.torrent_info('ttmp.dat').info_hash())
        # mangetlink = magneturi.from_torrent_data(data)
        # mangetlink = mangetlink[mangetlink.find('btih') + 5:mangetlink.find('btih') + 5 + 32]
        # b16Hash = base64.b16encode(base64.b32decode(mangetlink))
        # b16Hash = b16Hash.lower()
        # b16Hash = str(b16Hash, "utf-8")
        # return b16Hash
    except BaseException as e:
        gl.get_value('logger').logger.exception(traceback.format_exc())


if __name__ == '__main__':
    print('oringin file')
    print('libtorrent:' + str(libtorrent.torrent_info('123.torrent').info_hash()))
    mangetlink = magneturi.from_torrent_data(open('123.torrent', 'rb').read())
    mangetlink = mangetlink[mangetlink.find('btih') + 5:mangetlink.find('btih') + 5 + 32]
    b16Hash = base64.b16encode(base64.b32decode(mangetlink))
    b16Hash = b16Hash.lower()
    b16Hash = str(b16Hash, "utf-8")
    print('bencode:' + b16Hash)

    print('update file')
    print('libtorrent:' + str(libtorrent.torrent_info('new.torrent').info_hash()))
    mangetlink = magneturi.from_torrent_data(open('new.torrent', 'rb').read())
    mangetlink = mangetlink[mangetlink.find('btih') + 5:mangetlink.find('btih') + 5 + 32]
    b16Hash = base64.b16encode(base64.b32decode(mangetlink))
    b16Hash = b16Hash.lower()
    b16Hash = str(b16Hash, "utf-8")
    print('bencode:' + b16Hash)
    torrent = open('123.torrent', 'rb').read()
