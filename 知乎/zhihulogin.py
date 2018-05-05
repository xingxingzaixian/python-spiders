# -*- coding: utf-8 -*-

import random
import requests
from requests_toolbelt import MultipartEncoder
import hmac, time
from hashlib import sha1
import base64
from PIL import Image
import urllib3
urllib3.disable_warnings()

class ZhihuLogin(object):
    def __init__(self, phonenumber, password):
        self.phonenumber = phonenumber
        self.password = password
        self.session = requests.session()
        self.session.verify = False
        self.session.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36",
        }

    def encry_signature(self, time_span):
        sk = "d1b964811afb40118a12068ff74a12f4"
        h = hmac.new(sk.encode(), "password".encode(), sha1)
        h.update("c3cef7c66a1843f8b3a9e6a1e3160e20".encode())
        h.update("com.zhihu.web".encode())
        h.update(time_span.encode())
        return h.hexdigest()

    def random_boundary(self):
        factor = "ABCDEFGHIGKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        boundary = "----WebKitFormBoundary{}".format("".join(random.choices(factor, k=16)))
        return boundary

    def home_url(self):
        url = "https://www.zhihu.com/"
        self.session.get(url)
        print(10000, url)

    def get_captcha(self):
        captcha = ""
        url = "https://www.zhihu.com/api/v3/oauth/captcha?lang=en"
        self.session.headers["Authorization"] = "oauth c3cef7c66a1843f8b3a9e6a1e3160e20"
        r = self.session.get(url)
        result = r.json()
        if not result.get("show_captcha"):
            return ""
        else:
            while True:
                r = self.session.put(url)
                result = r.json()
                imgdata = base64.b64decode(result.get("img_base64"))
                with open("cap.png", "wb") as fp:
                    fp.write(imgdata)
                im = Image.open("cap.png")
                im.show()
                captcha = input("输入验证码>>")

                #验证码
                boundary = self.random_boundary()
                cap_data = MultipartEncoder(fields={"input_text":captcha}, boundary=boundary)
                self.session.headers["Content-Type"] = cap_data.content_type
                r = self.session.post(url, data=cap_data.to_string())
                result = r.json()
                if not result.get("error", None):
                    print("验证码正确")
                    break
                else:
                    print(result.get("error").get("message"))
            return captcha

    def login_post(self):
        captcha = self.get_captcha()
        time_span = str(int(time.time() * 1000))
        data = {
            "client_id":"c3cef7c66a1843f8b3a9e6a1e3160e20",
            "grant_type":"password",
            "timestamp":time_span,
            "source":"com.zhihu.web",
            "signature":self.encry_signature(time_span),
            "username":"+86" + self.phonenumber,
            "password":self.password,
            "captcha":captcha,
            "lang":"en",
            "ref_source":"homepage",
            "utm_source":""
        }

        boundary = self.random_boundary()
        encode_data = MultipartEncoder(data, boundary=boundary)
        self.session.headers["Content-Type"] = encode_data.content_type

        if self.session.cookies.get("_xsrf", None):
            self.session.headers["X-Xsrftoken"] = self.session.cookies.get("_xsrf")
        if self.session.cookies.get("d_c0", None):
            self.session.headers["X-UDID"] = self.session.cookies.get("d_c0").split("|")[0].strip('"')

        login_url = "https://www.zhihu.com/api/v3/oauth/sign_in"
        r = self.session.post(login_url, data=encode_data.to_string())
        result = r.json()
        if not result.get("error", None):
            print(result)
            return True
        else:
            print(result.get("error").get("message"))
            return False

    def visit_user_info(self):
        url = "https://www.zhihu.com/people/wan-rou-2"
        r = self.session.get(url)
        print(r.text)

if __name__ == "__main__":
    zhihu = ZhihuLogin(phonenumber, password)
    zhihu.home_url()
    if zhihu.login_post():
        zhihu.visit_user_info()
