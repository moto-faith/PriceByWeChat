# -*- coding: utf-8 -*-
import scrapy
import re
from scrapy.http import Request
from ..items import BookItem
from scrapy_redis.spiders import RedisCrawlSpider


class DangSpider(RedisCrawlSpider):
    name = "dang"
    allowed_domains = ["dangdang.com"]
    redis_key = "myspider:start_urls"

    # start_urls = ['http://category.dangdang.com/cp01.00.00.00.00.00-shbig.html']
  #  lpush myspider:start_urls http://category.dangdang.com/cp01.00.00.00.00.00-shbig.html
    def parse(self, response):
        tagsurl = response.xpath('//li[@dd_name="分类"]//div[@class="clearfix"]/span/a/@href').extract()
        tagsname = response.xpath('//li[@dd_name="分类"]//div[@class="clearfix"]/span/a/text()').extract()
        for tagurl, tagname in zip(tagsurl, tagsname):
            for i in range(1, 101):
                url = 'http://category.dangdang.com/pg{}-'.format(i) + tagurl[1:]
                yield Request(url=url, callback=self.listbook, meta={'tag': tagname})

    def listbook(self, response):
        tag = response.meta['tag']
        i = BookItem()
        url = response.xpath('//a[@dd_name="单品标题"]/@href').extract()
        name = response.xpath('//a[@dd_name="单品标题"]/text()').extract()
        price = response.xpath('//span[@class="search_now_price"]/text()').extract()
        i['tag'] = tag
        for i['url'], i['name'], i['price'] in zip(url, name, price):
            i['price'] = i['price'].replace('¥', '')
            yield i
