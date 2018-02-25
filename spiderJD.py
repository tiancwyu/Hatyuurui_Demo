__author__ = 'tiancwyu'
# -*- coding:utf-8 -*-

import requests
import chardet
import re

class spiderJD(object):
    """爬去京东商品评论数"""
    HEADER  = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Connection': 'keep-alive',
        'Accept-Encoding': 'gzip, deflate, br'
    }
    PROXIES  = {'http' : 'http://fxsl01872:qazwsx123@13.187.24.60:8000/'}
    TIME_OUT = 1000

    def getContent(self, url):
        try:
            r = requests.get(url= url, headers= self.HEADER, proxies= self.PROXIES, timeout= self.TIME_OUT)
            # print('Chardet Encoding: %s' %(chardet.detect(r.content)['encoding']))
            r.encoding = chardet.detect(r.content)['encoding']
            # print('response of %s is: %s' %(url, r.status_code))
            if not r.ok:
                print(r.status_code)
                raise ConnectionError
            else:
                return r.text
        except Exception as e:
            print('ERROR OCCUR!! Currrent get URL: %s' %(url))
            print(repr(e))
            return None

    def parseNum(self, idP):
        comment_url = "http://club.jd.com/comment/productPageComments.action?callback=fetchJSON_comment98vv242544&productId=" + idP + "&score=0&sortType=5&page=0&pageSize=10&isShadowSku=0&fold=1"
        raw = self.getContent(comment_url)
        pattern = re.compile(r'.*?commentCount":(.*?)\,.*?referenceName":"(.*?)"', re.S)
        data = re.findall(pattern, raw)
        try:
            strNum = data[0][1] + ':' + data[0][0]
            return strNum
        except Exception as e:
            print(idP)
            print(data)
            return None
        # print(strNum)

    def getUrl(self, url):
        resPage = self.getContent(url)
        patMaxPage = re.compile(r'.*?<b class="pn-break "> …</b>.*?<a href="(.*?page=).*?(\&.*?)" class.*?>(.*?)<', re.S)
        maxPage = re.findall(patMaxPage, resPage)
        patId = re.compile(r'.*?j-sku-item" data-sku="(.*?)"', re.S)
        id1 = re.findall(patId, resPage)
        for x in range(2, (int(maxPage[0][2]) + 1)):
            strUrl = "http://list.jd.com" + maxPage[0][0] + str(x) + maxPage[0][1]
            print(strUrl)
            resId = self.getContent(strUrl)
            id1 = id1 + re.findall(patId, resId)
        id2 = list(set(id1))
        return id2

    def run(self, urlPage):
        fo = open("foo.txt", "w", encoding='utf-8')
        listId = self.getUrl(urlPage)
        for id in listId:
            num = self.parseNum(id)
            if num != None:
                try:
                    fo.write(num)
                    fo.write("\n")
                except Exception as e:
                    print('ERROR OCCUR!! When write files, id: %s' %(id))
                    print(repr(e))
        fo.close()
        print("The Work is Done!")

if __name__ == '__main__':
    # a = spiderJD();
    # a.run('http://list.jd.com/list.html?cat=670,592,700&ev=exbrand_14073&delivery_glb=1&sort=sort_totalsales15_desc&trans=1&debug=cluster&JL=3_%E5%93%81%E7%89%8C_%E6%99%AE%E8%81%94%EF%BC%88TP-LINK%EF%BC%89#J_crumbsBar')
    list1 = ['TP-LINK TL-WR890N千兆版 450M无线路由器（全金属机身） 光纤宽带穿墙千兆有线端口:670000',
            'NULL TL-WDR7300千兆版 2100M 11AC双频无线路由器 千兆有线端口 光纤宽带WIFI穿墙:430000',
            'HUAWEI TL-WDR8610 2600M 11AC双频千兆无线路由器 千兆有线端口 板阵天线智能路由 上门安装套装:9600',
            'aaa TP-LINK TL-AP302C-PoE 300M企业级无线吸顶式AP 无线wifi接入点:22000',
            'NULL TL-AP451C 450M企业级无线吸顶式AP 无线wifi接入点:22000'
            ]

    list2 = []
    for title in list1:
        try:
            i = title.index('TP-LINK')
            titleL = list(title)
            titleL.insert(i+7,':')
            newS = ''.join(titleL)
            list2.append(newS)
            continue
        except Exception as e:
            print(repr(e))
        try:
            i = title.index('HUAWEI')
            titleL = list(title)
            titleL.insert(i+6,':')
            newS = ''.join(titleL)
            list2.append(newS)
        except Exception as e:
            pass
    print(list2)
