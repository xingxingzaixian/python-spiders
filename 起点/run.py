# -*- coding: utf-8 -*-
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

#获取settings模块的设置
from qidian.spiders.qidian import QidianSpider

settings = get_project_settings()
process = CrawlerProcess(settings=settings)

# 可以添加多个spider
process.crawl(QidianSpider)

#启动爬虫，会阻塞，知道爬取完成
process.start()
