# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import pymongo


class MongoPipeline(object):

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db
        self.discountMoney = 10

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DB')
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def you_hui(self, item, subMoney):
        Discount = self.db['Discount']
        dic = dict(item)
        dic['subMoney'] = subMoney
        Discount.insert(dic)

    def process_item(self, item, spider):

        name = item.__class__.__name__
        item['price'] = float(item['price'])
        res = self.db[name].find_one({'url': item['url']})
        if res == None: #如果数据库没有就添加
            self.db[name].insert(dict(item))
            return item
        flag = self.db[name].update({'url': item['url']}, dict(item))#判断是否更新了数据库
        subMoney = res['price'] - item['price']
        if flag['nModified'] and subMoney > self.discountMoney:
            self.you_hui(item, subMoney)# 数据库发生了更新且价格符合就放入今日优惠数据库
        return item

    def close_spider(self, spider):
        self.client.close()
