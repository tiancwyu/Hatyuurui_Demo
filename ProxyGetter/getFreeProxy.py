__author__ = 'tiancwyu'
# -*- coding:utf-8 -*-
"""
-------------------------------------------------
    File Name   : GetFreeProxy.py
    Description : 抓取免费代理
    Author      : tiancwyu
    date        : 2017/03/02
-------------------------------------------------
    Change Activity:
                    2017/03/02: Creat File
-------------------------------------------------
"""

import gevent
from gevent.pool import Pool
from lxml import etree
import requests
import spiderConfig
import chardet
import os
import re
import js2py


class proxySpider():
    """docstring for proxySpider"""
    HEADER = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.110 Safari/537.36',
        'Accept': 'ext/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8',
        'Connection': 'keep-alive',
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Upgrade-Insecure-Requests':'1'
    }
    KUAICOOKIES = {}
    TMPHEADER = {}

    def __init__(self, queueRow):
        self.queueRow = queueRow
        # 创建一个无序不重复元素集用来存放proxy
        self.proxies = set()

    def getContent(self, url):
        self.TMPHEADER = spiderConfig.HEADER
        try:
            r = requests.get(url= url, headers= headers, proxies= spiderConfig.PROXIES, timeout= spiderConfig.TIME_OUT)
            r.encoding = chardet.detect(r.content)['encoding']
            # print('response of %s is: %s' %(url, r.status_code))
            if not r.ok:
                raise ConnectionError
            else:
                return r.text
        except Exception as e:
            if r.status_code == 521:
                pattern1 = re.compile(r'.*?\(.*?\((.*?)\).*?(function.*?)eval\("qo=eval;', re.S)
                code = re.findall(pattern1, r.text)
                func = js2py.eval_js(code[0][1] + 'return po;}')
                pattern2 = re.compile(r'.*?(_.*?)=(.*?);')
                cookiesValue =  re.findall(pattern2, func(int(code[0][0])))
                self.KUAICOOKIES[cookiesValue[0][0]] = cookiesValue[0][1]
                r = requests.get(url= url, headers= headers, proxies= spiderConfig.PROXIES, timeout= spiderConfig.TIME_OUT, cookies= self.KUAICOOKIES)
                r.encoding = chardet.detect(r.content)['encoding']
                if r.ok:
                    return r.text
                else:
                    print('ERROR OCCUR!! Currrent get URL: %s' %(url))
                    return None
            else:
                print('ERROR OCCUR!! Currrent get URL: %s' %(url))
                print(repr(e))
                return None

    def getProxyList(self, content, parser):
        if parser['type'] == 'lxml':
            pList       = []
            eContent    = etree.HTML(content)
            proxiesList = eContent.xpath(parser['pattern'])
            for proxy in proxiesList:
                proxyDetil  = {'ip':'','port':'','country':'','type':''}
                proxyDetil['ip']      = proxy.xpath(parser['position']['ip'])[0].text
                proxyDetil['port']    = proxy.xpath(parser['position']['port'])[0].text
                proxyDetil['type']    = proxy.xpath(parser['position']['type'])[0].text
                proxyDetil['country'] = proxy.xpath(parser['position']['country'])[0].text
                pList.append(proxyDetil)
            return pList
        else:
            print('proxySpider: This kind of type does not support now!')
            return None

    def saveProxy(self, pList):
        str1 = '\n----------------------\n'
        if not os.path.exists('porxieslist.txt'):
            f = open('porxieslist.txt', 'wb')
        else:
            f = open('porxieslist.txt', 'ab')
        for proxy in pList:
            # print(proxy['ip'])
            for key in proxy.keys():
                # result = etree.tostring(i, encoding="utf-8", pretty_print=True, method="html")
                str2 = str(key) + '= ' + str(proxy[key]) + '\t'
                f.write(str2.encode(encoding="utf-8"))
            f.write(str1.encode(encoding="utf-8"))
        f.close()

    def run(self, url, parser):
        content   = self.getContent(url)
        # if content is not None:
        #     pList = self.getProxyList(content, parser)
        #     if pList is not None:
        #         for proxy in pList:
        #             proxy_str = '%s:%s' % (proxy['ip'], proxy['port'])
        #             if proxy_str not in self.proxies:
        #                 self.proxies.add(proxy_str)

    def getSet(self):
        return self.proxies
        # self.saveProxy(proxyList)