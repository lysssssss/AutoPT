import magneturi
import base64
import globalvar as gl


def get_torrent_hahs40(data):
    try:
        mangetlink = magneturi.from_torrent_data(data)
        mangetlink = mangetlink[mangetlink.find('btih') + 5:mangetlink.find('btih') + 5 + 32]
        b16Hash = base64.b16encode(base64.b32decode(mangetlink))
        b16Hash = b16Hash.lower()
        b16Hash = str(b16Hash, "utf-8")
        return b16Hash
    except BaseException as e:
        gl.get_value('logger').logger.error(e)
