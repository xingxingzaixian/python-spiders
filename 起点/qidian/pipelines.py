# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import pymongo
import redis

class QidianRedisPipeline(object):
    def open_spider(self, spider):
        self.redis = redis.Redis(host='localhost', port=6379, db=0)

    def process_item(self, item, spider):
        if self.redis.sismember("qidian_data", item["name"]):
            return
        self.redis.sadd("qidian_data", item["name"])
        return item

class QidianPipeline(object):
    collection_name = 'qidian'
    collection_name_dup = 'qidian_dup'

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        #  必须在settings中 配置 MONGO_URI 和 MONGO_DATABASE
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            # items 是默认值，如果settings当中没有配置 MONGO_DATABASE ，那么 mongo_db = 'items'
            mongo_db=crawler.settings.get('MONGO_DATABASE', 'items')
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        self.db[self.collection_name].insert_one(dict(item))
        return item
