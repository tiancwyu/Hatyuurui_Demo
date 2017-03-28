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

import requests
import time
import spiderConfig
import json
import gevent
from multiprocessing import Process
from DB.MySQLManager import MySQLManager

def getMyIp():
    try:
        r  = requests.get(url= spiderConfig.TEST_IP, headers= spiderConfig.HEADER, timeout= spiderConfig.TIME_OUT)
        ip = json.loads(r.text)
        return ip['origin']
    except Exception as e:
        raise e

def checkProxyDetil(selfip, proxy, isHttp = True):
    '''
    判断代理IP的有效性及相关参数：
    有效性：使用requests.get()请求连接，如果超时，则认为是无效IP
    协议：分别用http| https组成url进行requests.get(),根据请求结果判断代理所使用的协议
    speed：根据开始请求的时间及请求结束的时间判断代理的连接速度
    type：超代 high anonymous(level 0)：x_forwarded_for & x_real_ip都不显示，服务器察觉不到你
                                        在使用代理
          匿名 anonymous(level 1)：x_forwarded_for & x_real_ip中为代理服务器的IP，隐藏了您的
                                   真实IP，但是向服务器透露了您是使用代理服务器访问他们的。
          透明 transparent(level 2)：x_forwarded_for & x_real_ip中为你的真实IP地址
    '''
    types = -1
    speed = -1    
    if isHttp:
        test_url = spiderConfig.TEST_HTTP_HEADER
    else:
        test_url = spiderConfig.TEST_HTTPS_HEADER

    try:
        start = time.time()
        r = requests.get(url= test_url, headers= spiderConfig.HEADER, timeout= spiderConfig.TIME_OUT, proxies= proxy)
        if r.ok:
            speed = round(time.time()- start, 2)
            # json.loads: 将json格式解码成python的dict格式
            content = json.loads(r.text)
            headers = content['headers']
            ip = content['origin']

            # X-Forwarded-For 请求头格式非常简单，就这样：X-Forwarded-For: client, proxy1, proxy2
            # 如果一个 HTTP 请求到达服务器之前，经过了三个代理 Proxy1、Proxy2、Proxy3，IP 分别为 IP1、IP2、IP3，用户真实 IP 为 IP0，那么按照 XFF 标准，服务端最终会收到以下信息：
            # X-Forwarded-For: IP0, IP1, IP2
            x_forwarded_for = headers.get('X-Forwarded-For', None)
            x_real_ip = headers.get('X-Real-Ip', None)

            if selfip in ip or ',' in ip:
                return False, types, speed
            elif x_forwarded_for is None and x_real_ip is None:
                types = 0
            elif selfip not in x_forwarded_for and selfip not in x_real_ip:
                types = 1
            else:
                types = 2
            return True, types, speed
        else:
            return False, types, speed
    except Exception as e:
        return False, types, speed

def checkProxy(selfip, proxy):
    '''
    用来检测代理的类型，突然发现，免费网站写的信息不靠谱，还是要自己检测代理的类型
    protocol : http(0)   https(1)   两者都支持(2)
    types：    超代(0)  匿名(1)     透明(2)
    speed：链接速度
    '''
    protocol   = -1
    types      = -1
    speed      = -1
    ip         = proxy['ip']
    port       = proxy['port']
    httpProxy  = {'http': 'http://%s:%s'%(ip,port)}
    httpsProxy = {'https': 'https://%s:%s'%(ip,port)}
    http, http_types, http_speed    = checkProxyDetil(selfip, httpProxy, True)
    https, https_types, https_speed = checkProxyDetil(selfip, httpsProxy, False)

    if http and https:
        protocol   = 2
        types      = http_types
        speed      = http_speed
    elif http:
        protocol   = 0
        types      = http_types
        speed      = http_speed
    elif https:
        protocol   = 1
        types      = https_types
        speed      = https_speed
    else:
        protocol   = -1
        types      = -1
        speed      = -1
    return protocol, types, speed

def detectProxy(selfip, proxy, queueOK=None):
    '''
    检测IP属性，依据结果更新信息或将无效IP抛弃
    '''
    protocol, types, speed = checkProxy(selfip, proxy)
    if protocol >= 0:
        proxy['protocol'] = protocol
        proxy['type'] = types
        proxy['speed'] = speed
    else:
        proxy = None

    if queueOK:
        queueOK

    return proxy

def coroutineStart(proxies, myip, queueOK):
    '''
    由于IP检测速度应网络条件不同耗时各异，为加快速度，采用协程处理
    '''
    spawns = []
    for proxy in proxies:
        spawns.append(gevent.spawn(detectProxy, myip, proxy, queueOK))
    # 所有子协程运行结束后再执行父进程
    gevent.joinall(spawns)

def checker(queueOrigin, queueOK, myip):
    '''
    验证代理地址的有效性
    不断的从queueOrigin中取出IP进行验证，并将有效IP存入queueOK中
    '''
    proxies = []
    while True:
        try:
            # 不停的从队列中取出原始IP,每取一个，将进程暂停10ms，防止取得太快来不及处理，当取满500个后，验证有效性
            proxy = queueOrigin.get(timeout= 10)
            proxies.append(proxy)
            if len(proxies) > 500:
                # 因为本子进程不停地从队列中取值，所以验证工作需要新开一个子进程来处理
                p = Process(target= coroutineStart, args= (proxies, queueOK, myip))
                p.start
                proxies = []
        except Exception as e:
            # 如果发生错误，就不必等到500个，先将已经取出的IP进行验证，再从0开始
            if len(proxies) > 0:
                p = Process(target= coroutineStart, args= (proxies, queueOK, myip))
                p.start
                proxies = []

def checkFromDb(myip, proxy, proxiesSet):
    '''
    验证数据库中IP的有效性并评分，依照结果更新数据库或从数据库中删除无效数据
    '''
    # result = checkProxy(myip, proxy)
    result = True
    if result:
        # 如果result不为None，则认为该IP还是有效的；
        # 同时将score加1，被检测次数越多，表明存在时间越长，则得分就应该越高,最高分60000
        if proxy['score'] < 60000:
            score = proxy['score'] + 1
        else:
            score = 60000
        sqlhelper = MySQLManager()
        sqlhelper.update({'ip': proxy['ip'], 'port': proxy['port']}, {'score': score})
    else:
        MySQLManager.delete({'ip': proxy['ip'], 'port': proxy['port']})


if __name__ == '__main__':
    proxy ={'ip': '13.187.27.175', 'port': 8080, 'score': 21}
    checkFromDb(0,proxy,0)
    # a = checkProxyDetil('118.151.184.238', proxies, True)
    # a =getMyIp()
