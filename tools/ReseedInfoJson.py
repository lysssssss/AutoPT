# -*- coding: utf-8 -*-
# @Time    : 2020/2/7 0:23
# @Author  : Eason Li
# @GitHub  : https://github.com/lysssssss
# @File    : ReseedInfoJson.py
# @Software: PyCharm
import json
import os


class ReseedInfoJson:
    def __init__(self):
        self._path = 'autopt/appdata/ReSeedRecord.json'
        if not os.path.exists(self._path):
            with open(self._path, 'w', encoding='UTF-8') as f:
                f.write('{}')

    def getdata(self):
        jsonlist = {}
        with open(self._path, 'r', encoding='UTF-8') as f:
            jsonlist = json.loads(f.read())
        return jsonlist

    def setdata(self, jsonlist):
        with open(self._path, 'w', encoding='UTF-8') as f:
            f.write(json.dumps(jsonlist))

    def changestatus(self, prhash, rshash, stauts):
        jsonlist = self.getdata()
        update = False
        for idx, rs in enumerate(jsonlist[prhash]['rslist']):
            if rs['hash'] == rshash:
                jsonlist[prhash]['rslist'][idx]['status'] = stauts
                update = True
                break
        if update:
            self.setdata(jsonlist)

    def addrstopr(self, prhash, rshash, rssname, rstid, rsstatus):
        jsonlist = self.getdata()
        if prhash in jsonlist:
            rslist = jsonlist[prhash]['rslist']
            isex = False
            isexidx = -1
            for idx, val in enumerate(rslist):
                if val['hash'] == rshash:
                    isex = True
                    isexidx = idx
                    break
            if isex:
                jsonlist[prhash]['rslist'][isexidx] = {
                    'hash': rshash,
                    'tid': int(rstid) if isinstance(rstid, str) else rstid,
                    'sname': rssname,
                    # 'sid': getnamesid(rsname),
                    'status': rsstatus
                }
            else:
                # 添加辅种信息到主种
                rsinfo = {
                    'hash': rshash,
                    'tid': int(rstid) if isinstance(rstid, str) else rstid,
                    'sname': rssname,
                    # 'sid': getnamesid(rsname),
                    'status': rsstatus
                }
                rslist.append(rsinfo)
        else:
            jsonlist[prhash] = {
                'info': {
                    'hash': prhash,
                    # 'sid': getnamesid(prname),
                    'tid': 0,
                    'sname': ''
                },
                'rslist': [{
                    'hash': rshash,
                    # 'sid': getnamesid(prname),
                    'tid': int(rstid) if isinstance(rstid, str) else rstid,
                    'sname': rssname,
                    'status': rsstatus
                }]
            }
        self.setdata(jsonlist)

    def addpr(self,prhash,prsname,prtid):
        jsonlist = self.getdata()
        jsonlist[prhash] = {
            'info': {
                'hash': prhash,
                # 'sid': getnamesid(prname),
                'tid': int(prtid) if isinstance(prtid, str) else prtid,
                'sname': prsname
            },
            'rslist': []
        }
        self.setdata(jsonlist)

    def findprhashbyhash(self, thash):
        jsonlist = self.getdata()
        newprhash = None
        if thash in jsonlist:
            newprhash = thash
        else:
            for key, value in jsonlist.items():
                for val in value['rslist']:
                    if thash == val['hash']:
                        newprhash = key
                        break
                if newprhash is not None:
                    break
        return newprhash

    def delpr(self,prhash):
        jsonlist = self.getdata()
        if prhash in jsonlist:
            del jsonlist[prhash]
            self.setdata(jsonlist)
