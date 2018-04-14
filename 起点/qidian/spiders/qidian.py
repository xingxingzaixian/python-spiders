# -*- coding: utf-8 -*-
import re
import scrapy
from lxml import etree
from io import BytesIO
from fontTools.ttLib import TTFont
from qidian import items
from scrapy.utils.project import get_project_settings
import pymongo
import redis
from hashlib import md5

WORD_MAP = {"zero":"0","one":"1","two":"2","three":"3","four":"4","five":"5","six":"6","seven":"7","eight":"8","nine":"9","period":"."}

class QidianSpider(scrapy.Spider):
    name = "qidian"
    allowed_domains = ['www.qidian.com', 'qidian.gtimg.com']
    start_urls = ["https://www.qidian.com/all?orderId=3&style=1&pageSize=20&siteid=1&pubflag=0&hiddenField=0"]

    def __init__(self):
        self.woff_dict = {}
        self.page_url = "https://www.qidian.com/all?orderId=3&style=1&pageSize=20&siteid=1&pubflag=0&hiddenField=0&page={}"
        settings = get_project_settings()
        self.client = pymongo.MongoClient(settings.get('MONGO_URI'))
        self.db = self.client[settings.get('MONGO_DATABASE', 'items')]
        self.redis = redis.Redis(host='localhost', port=6379, db=0)

    # def start_requests(self):
    #     yield scrapy.Request(self.page_url.format("1"), callback=self.parse_total)

    def parse(self, response):
        html = etree.HTML(response.text)
        page = html.xpath('//a[@class="lbf-pagination-page  "]')[-1]
        total_pages = int(page.text)

        for i in range(1, total_pages + 1):
            uuid = md5()
            uuid.update(self.page_url.format(i).encode())
            if self.redis.sismember("qidian_url", uuid.digest()):
                continue
            self.redis.sadd("qidian_url", uuid.digest())
            print(self.page_url.format(i))

            yield scrapy.Request(self.page_url.format(i), callback=self.parse_page)

    def parse_page(self, response):
        html = etree.HTML(response.text)
        woff_link = re.compile(r"\('eot'\); src: url\('(.*?).woff'\)")
        word_link = re.compile(r">(.*?);<")
        for each in html.xpath('//li[@data-rid]'):
            item = {}
            item.setdefault("url", response.url)
            item.setdefault("name", each.findtext("div/h4/a"))
            item.setdefault("author", each.findtext('div/p[@class="author"]/a'))
            item.setdefault("status", each.findtext('div/p[@class="author"]/span'))
            item.setdefault("update", each.findtext('div/p[@class="update"]/b'))

            # 获取文字数，并取出加密文字信息
            ele_word = each.find('div/p[@class="update"]/span/span')
            encry_text = etree.tostring(ele_word).decode()
            groups = word_link.search(encry_text)
            encry_text = groups.group(1)
            item.setdefault("encry_text", encry_text.strip(";"))

            # 获取自定义字体文件链接
            style = each.findtext('div/p[@class="update"]/span/style')
            groups = woff_link.search(style)
            woff_url = groups.group(1) + ".woff"
            if not woff_url.startswith("http"):
                woff_url = "http://" + woff_url

            if woff_url not in self.woff_dict:
                yield scrapy.Request(woff_url, callback=self.parse_detail, meta=item, priority=100)
            else:
                yield self.create_result(self.woff_dict.get(woff_url), item)

        # result_pages = html.xpath('//li[@class="lbf-pagination-item"]/a[@data-page]')
        # for item in result_pages:
        #     page = item.get('data-page')
        #     page_url = self.page_url.format(page)
        #     m = md5()
        #     m.update(page_url.encode())
        #     if self.redis.sismember(m.digest()):
        #         continue
        #
        #     print(page_url)
        #     yield scrapy.Request(page_url, callback=self.parse_page)

    def parse_detail(self, response):
        print(response.url)
        font = TTFont(BytesIO(response.body))
        cmap = font.getBestCmap()
        font.close()

        self.woff_dict.setdefault(response.url, cmap)

        return self.create_result(cmap, response.meta)

    def create_result(self, cmap, meta):
        word_count = ""
        encry_text = meta.get("encry_text")
        for flag in encry_text.split(";"):
            ch = cmap.get(int(flag[2:]))  # 去掉前面的&#
            word_count += WORD_MAP.get(ch, "")

        item = items.QidianItem()
        item['url'] = meta["url"]
        item['name'] = meta["name"]
        item['author'] = meta["author"]
        item['status'] = meta["status"]
        item['update'] = meta["update"]
        item['words'] = word_count
        return item