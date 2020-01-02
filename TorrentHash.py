import traceback
import libtorrent
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

    with open('123.torrent', 'rb') as f:
        aaa = f.read()
        print(get_torrent_hash40(aaa))
