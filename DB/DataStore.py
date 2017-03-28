__author__ = 'tiancwyu'
# -*- coding:utf-8 -*-
"""
-------------------------------------------------
    File Name   : DataStore.py
    Description : 将数据存入数据库中
    Author      : tiancwyu
    date        : 2017/03/09
-------------------------------------------------
    Change Activity:
                    2017/03/09: Creat File
-------------------------------------------------
"""

import DB.MySQLManager


class storeData():
    '''
    读取队列中的数据，写入数据库中
    '''
    def __init__(self, arg):
        super(storeData, self).__init__()
        self.arg = arg
        