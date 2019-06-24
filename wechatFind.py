# -*- coding:utf-8 -*-
import requests
import json
import itchat
import requests
import re
from lxml import etree
from pymongo import *
from urllib3 import encode_multipart_formdata

# 连接
client = MongoClient(host='localhost', port=27017)
# 选择库
db = client.books
# 选择集合
test_set = db.Discount



def low_price(url):
    product_url = url
    url = 'http://p.zwjhl.com/price.aspx?url={}'.format(product_url)
    response = requests.get(url).text
    if '该商品暂未收录' in response:
        return '该商品暂未收录'
    sel = etree.HTML(response)
    lower_price_date = sel.xpath('//div[@class="bigwidth"]//font[3]/text()')[0].strip().replace('(', '').replace(')','').replace('/', '-')
    lower_price = sel.xpath('//font[@class="bigwordprice"]/text()')[0].strip()
    now_price = sel.xpath('//div[@class="bigwidth"]/span/text()[5]')[0].strip()

    return '''最低价格:{}\n最低价格日期:{}\n{}'''.format(lower_price, lower_price_date, now_price)



def taobao_url(text):
    kouling = re.findall('(￥.*?￥)', text)[0]
    url = 'https://api.open.21ds.cn/apiv1/jiexitkl?apkey=072208b0-b809-ad71-4203-3f8c90e0f78f&kouling={}'.format(kouling)
    response = requests.get(url).text
    true_url = json.loads(response)['data']['url']
    return true_url

def todayBest():
    bestProduct = test_set.find().sort([("subMoney", -1)])[0]
    bestProductName = bestProduct['name']
    bestProductPrice = bestProduct['price']
    bestProductUrl = bestProduct['url']
    bestProductSubMoney = bestProduct['subMoney']
    message = "商品名称：" + bestProductName + "\n商品价格：" + str(
        bestProductPrice) + "元\n商品链接：" + bestProductUrl + "\n降价幅度：" + str(bestProductSubMoney) + "元"
    return message

def auto_chat(text):
    data = {
        "perception": {
            "inputText": {
                "text": text
            }
        },
        "userInfo": {
            "apiKey": "dde9f4256d5849c18f98821eaf908db4",
            "userId": '123',
        }
    }
    req = json.dumps(data).encode('utf8')
    r = requests.post('http://openapi.tuling123.com/openapi/api/v2', data=req).text
    print(r)
    r=json.loads(r)['results']
    for resutl in r:
        return resutl['values']['text']

@itchat.msg_register('Text',isGroupChat=False)
def text_reply(msg):
    content = msg['Content']
    fromuser = msg['FromUserName']
    print(content)
    try:
        try:
            compact = re.findall("(.*?)\s(\d+)元", content)[0]
            tag = compact[0]
            money = float(compact[1])
            try:
                product = test_set.find({"tag": tag, "price": {"$lte": money}}).sort([("subMoney", -1)])[0]
                bestProductName = product['name']
                bestProductPrice = product['price']
                bestProductUrl = product['url']
                bestProductSubMoney = product['subMoney']
                message = "商品名称：" + bestProductName + "\n商品价格：" + str(
                    bestProductPrice) + "元\n商品链接：" + bestProductUrl + "\n降价幅度：" + str(bestProductSubMoney) + "元"

            except:
                message = "没查到价格内商品"
        except:
            if '寳' in content:
                url = taobao_url(content)
                message = low_price(url)
            elif 'http' in content:
                message = low_price(content)
            elif '今日优惠' in content:
                message = todayBest()
            else:
                message = auto_chat(content)
    except:
        message = "对不起，您说的我没听明白。"
    print(message)
    itchat.send(message,fromuser)

@itchat.msg_register(itchat.content.PICTURE,isGroupChat=False)
def img_reply(msg):
    msg.download(msg['FileName'])
    content = msg['Content']
    fromuser = msg['FromUserName']
    data = {}
    header = {}
    data['file'] = (msg['FileName'], open(msg['FileName'], 'rb').read())
    encode_data = encode_multipart_formdata(data)
    data = encode_data[0]
    header['Content-Type'] = encode_data[1]
    res = requests.post("https://search.jd.com/image?op=upload", headers=header, data=data).text
    path = re.findall('"(.*?)"', res)[1]
    url = "https://search.jd.com/image?path="+path+"&op=search"
    ItemRes = requests.get(url)
    ItemRes.encoding = "utf-8"
    sel = etree.HTML(ItemRes.text)
    name = sel.xpath('//li[1]//div[@class="p-name p-name-type3"]/a/em/text()')[0]
    href = "http:"+sel.xpath('//li[1]//div[@class="p-name p-name-type3"]/a/@href')[0]
    message = name+"\n"+href+"\n"+low_price(href)
    print(message)
    itchat.send(message, fromuser)

itchat.auto_login(hotReload=True)
itchat.run()