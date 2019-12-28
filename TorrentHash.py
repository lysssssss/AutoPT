import base64
import traceback
import magneturi

import globalvar as gl


def get_torrent_hash40(data):
    try:
        mangetlink = magneturi.from_torrent_data(data)
        mangetlink = mangetlink[mangetlink.find('btih') + 5:mangetlink.find('btih') + 5 + 32]
        b16Hash = base64.b16encode(base64.b32decode(mangetlink))
        b16Hash = b16Hash.lower()
        b16Hash = str(b16Hash, "utf-8")
        return b16Hash
    except BaseException as e:
        gl.get_value('logger').logger.exception(traceback.format_exc())


# if __name__ == '__main__':
#     torrent = open('123.torrent', 'rb').read()
#     print(get_torrent_hash40(torrent))
#     # 计算meta数据
#     metadata = bencode.bdecode(torrent)
#     hash_content = bencode.bencode(metadata[b'info'])
#     digest = hashlib.sha1(hash_content).digest()
#     b32hash = base64.b32encode(digest)
#     print(b32hash.decode())
#     b16Hash = base64.b16encode(base64.b32decode(b32hash.decode()))
#     b16Hash = b16Hash.lower()
#     b16Hash = str(b16Hash, "utf-8")
#     print(b16Hash)

