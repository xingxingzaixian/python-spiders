# -*- coding: utf-8 -*-
import json
import random
import re
from urllib import parse

import binascii
import math
import requests
import time
import urllib3
import base64
import rsa
from lxml import etree
from config import USER_NAME, PASSWORD

urllib3.disable_warnings()

class WeiBo(object):
    def __init__(self):
        self.session = requests.session()
        self.session.verify = False
        self.session.headers = {
            "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36"
        }

    @staticmethod
    def user_encrypt(user):
        user = parse.quote(user)
        user = base64.b64encode(user.encode())
        return user

    @staticmethod
    def pass_encrypt(password, servertime, nonce, pubKey):
        message = str(servertime) + "\t" + str(nonce) + "\n" + password
        rsa_n = int(pubKey, 16)
        rsa_e = int("10001", 16)
        key = rsa.PublicKey(rsa_n, rsa_e)
        pass_key = rsa.encrypt(message.encode(), key)
        return binascii.b2a_hex(pass_key).decode()

    def login_init(self):
        url = r"https://weibo.com/login.php"
        resp = self.session.get(url)
        link = re.compile(r'feed/index.js?version=(.*?)"')
        groups = link.search(resp.text)
        version = groups.group(0)

        url = r'https://js1.t.sinajs.cn/t5/register/js/v6/pl/register/loginBox/index.js?version={}'.format(version)
        resp = self.session.get(url)

    def prelogin_param(self):
        params = {
            "entry":"weibo",
            "callback":"sinaSSOController.preloginCallBack",
            "su": self.user_encrypt(USER_NAME),
            "rsakt": "mod",
            "checkpin":"1",
            "client":"ssologin.js(v1.4.19)",
            "_":int(time.time() * 1000)
        }
        url = r"https://login.sina.com.cn/sso/prelogin.php"
        resq = self.session.get(url, params=params)
        link = re.compile(r'({.*?})')
        groups = link.search(resq.text)
        pre_dict = eval(groups.group(0))
        return pre_dict.get('pcid'), pre_dict.get('servertime'),pre_dict.get('nonce'),pre_dict.get('pubkey'),pre_dict.get('rsakv')

    def get_qrcode(self, pcid):
        params = {
            "r":math.floor(random.random() * math.pow(10, 8)),
            "s":"0",
            "p": pcid
        }
        url = r"https://login.sina.com.cn/cgi/pin.php"
        resp = self.session.get(url, params=params)
        with open("qrcode.png", 'wb') as fp:
            fp.write(resp.content)

        qrcode = input(">>>")
        return qrcode

    def submit_login(self, servertime, nonce, pubKey, rsakv, pcid):
        qrcode = self.get_qrcode(pcid)
        print(qrcode)
        sp = self.pass_encrypt(PASSWORD, servertime, nonce, pubKey)
        data = {
            "entry":"weibo",
            "gateway":"1",
            "from":"",
            "savestate":"0",
            "qrcode_flag":"false",
            "useticket":"1",
            "pagerefer":"",
            "pcid":pcid,
            "door":qrcode,
            "vsnf":"1",
            "su":self.user_encrypt(USER_NAME),
            "service":"miniblog",
            "servertime":servertime,
            "nonce":nonce,
            "pwencode":"rsa2",
            "rsakv":rsakv,
            "sp": sp,
            "sr":"1600*900",
            "encoding":"UTF-8",
            "prelt":random.randint(100,500),
            "url":"https://weibo.com/ajaxlogin.php?framelogin=1&callback=parent.sinaSSOController.feedBackUrlCallBack",
            "returntype":"META"
        }
        url = r"https://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.19)"
        resq = self.session.post(url, data=data)
        link = re.compile(r'location.replace\("(.*?)"\);')
        groups = link.search(resq.text)
        url = groups.group(1)
        print(10001, url)
        resq = self.session.get(url)
        link = re.compile(r"location.replace\('(.*?)'\)")
        groups = link.search(resq.text)
        url = groups.group(1)
        print(10002, url)
        resq = self.session.get(url)
        print(10003, resq.url, resq.status_code)
        link = re.compile(r"{.*?}}")
        groups = link.search(resq.text)
        response_con = groups.group(0)
        print(10004, response_con)
        result_dict = json.loads(response_con)
        if not result_dict.get('result'):
            print(response_con)
            return
        userdomain = result_dict.get('userinfo').get('userdomain')
        url = r"https://weibo.com/{}".format(userdomain)
        response = self.session.get(url)

        #查找微博昵称
        if response.text.find("small_bud") != -1:
            print(10005, "Login Success")
        else:
            print(30001, "Login Failed")
            return

        if response.text.find('small_bud') != -1:
            print("登录成功")
        else:
            print("登录失败")

        #获取关注者
        link = re.compile(r'<strong node-type=.*?follow.*?>(\d+)<.*?>')
        groups = link.search(response.text)
        print("Follow: ", groups.group(1))

        #获取粉丝数
        link = re.compile(r'<strong node-type=.*?fans.*?>(\d+)<.*?>')
        groups = link.search(response.text)
        print("Fans", groups.group(1))

if __name__ == "__main__":
    weibo = WeiBo()
    pcid, servertime, nonce, pubkey, rsakv = weibo.prelogin_param()
    weibo.submit_login(servertime, nonce, pubkey, rsakv, pcid)