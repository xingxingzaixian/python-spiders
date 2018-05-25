# -*- coding: utf-8 -*-
import json
import requests
import urllib3
from lxml import etree
urllib3.disable_warnings()

from selenium_cnblog import analog_login

class CNBlog(object):
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session = requests.session()
        self.session.verify = False
        self.session.headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.1 Safari/605.1.15"
        }

    # 检测cookies是否有效
    def check_cookies_valid(self):
        try:
            cookies_dict = {}
            with open('cookies.txt') as fp:
                cookies = json.load(fp)
                for cookie in cookies:
                    cookies_dict.setdefault(cookie['name'], cookie['value'])
        except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
            if analog_login(self.username, self.password):
                self.check_cookies_valid()
            return

        cookiesjar = requests.utils.cookiejar_from_dict(cookies_dict)
        self.session.cookies = cookiesjar
        r = self.session.get(r"https://home.cnblogs.com/u/small-bud/")
        r.encoding = "utf-8"
        # 如果cookies失效，则重新进行模拟登录
        if r.text.find("星星在线") == -1:
            #如果模拟登录成功，重新进行cookies检测
            if analog_login(self.username, self.password):
                self.check_cookies_valid()
            else:
                return False
        return True

    def send_chapter(self, file_name, title):
        with open(file_name, 'r', encoding='utf-8') as fp:
            content = fp.read()

        url = "https://i.cnblogs.com/EditPosts.aspx?opt=1"
        r = self.session.get(url)
        html = etree.HTML(r.text)
        __VIEWSTATE = html.xpath('//*[@id="__VIEWSTATE"]')[0].attrib.get('value')
        __VIEWSTATEGENERATOR = html.xpath('//*[@id="__VIEWSTATEGENERATOR"]')[0].attrib.get('value')

        data = {
            "__VIEWSTATE":__VIEWSTATE,
            "__VIEWSTATEGENERATOR":__VIEWSTATEGENERATOR,
            "Editor$Edit$txbTitle":title,
            "Editor$Edit$EditorBody":content,
            "Editor$Edit$Advanced$ckbPublished":"on",
            "Editor$Edit$Advanced$chkDisplayHomePage":"on",
            "Editor$Edit$Advanced$chkComments":"on",
            "Editor$Edit$Advanced$chkMainSyndication":"on",
            "Editor$Edit$Advanced$txbEntryName":"",   
            "Editor$Edit$Advanced$txbExcerpt":"",
            "Editor$Edit$Advanced$txbTag":"",
            "Editor$Edit$Advanced$tbEnryPassword":"",
            "Editor$Edit$lkbPost":"发布"
        }
        self.session.post(url, data=data)

        url = "http://www.cnblogs.com/small-bud/"
        r = self.session.get(url)
        if r.text.find(title) != -1:
            print("发布成功")

if __name__ == "__main__":
    cn = CNBlog("用户名", "密码")
    if cn.check_cookies_valid():
        cn.send_chapter("chapter.md", "博客园自动发帖--图像处理极验验证码")
