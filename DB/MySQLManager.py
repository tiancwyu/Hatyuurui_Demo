__author__ = 'tiancwyu'
# -*- coding:utf-8 -*-
"""
-------------------------------------------------
    File Name   : MySQLManager.py
    Description : 数据库操作相关函数
    Author      : tiancwyu
    date        : 2017/03/08
-------------------------------------------------
    Change Activity:
                    2017/03/08: Creat File
-------------------------------------------------
"""

import pymysql
import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base

BaseModel = declarative_base()

class IpProxies(BaseModel):
    '''
    定义数据库的基本格式，所包含的列名
    包括ip，端口，types类型(0高匿名，1透明)，protocol(0 http,1 https http),country(国家),area(省市),updatetime(更新时间)
     speed(连接速度),评分
    '''
    __tablename__ = 'IpProxies'
    id            = sqlalchemy.Column(sqlalchemy.Integer,      primary_key= True, autoincrement=True)
    ip            = sqlalchemy.Column(sqlalchemy.CHAR(15),     nullable= False)
    port          = sqlalchemy.Column(sqlalchemy.Integer,      nullable= False)
    types         = sqlalchemy.Column(sqlalchemy.Integer,      nullable= False)
    protocol      = sqlalchemy.Column(sqlalchemy.Integer,      nullable= False)
    country       = sqlalchemy.Column(sqlalchemy.CHAR(100),    nullable= False)
    area          = sqlalchemy.Column(sqlalchemy.CHAR(100),    nullable= False)
    updatetime    = sqlalchemy.Column(sqlalchemy.DATETIME(),   nullable= False)
    # Numeric(5,2)：定义浮点数，5为整数位数，2为小数位数
    speed         = sqlalchemy.Column(sqlalchemy.Numeric(5,2), nullable= False)
    score         = sqlalchemy.Column(sqlalchemy.Integer,      nullable= False)

class MySQLManager():
    '''
    SQL操作类，用来进行数据库的插入，修改，删除，选择
    '''
    params = {'ip': IpProxies.ip, 'port': IpProxies.port, 'types': IpProxies.types, 'protocol': IpProxies.protocol,
              'country': IpProxies.country, 'area': IpProxies.area, 'score': IpProxies.score}

    def __init__(self):
        # 连接需要操作的数据库(本程序中没有数据库创建语句，MyProxies必须是已经建好的); echo用于选择是否显示生成的SQL语句
        self.engine = sqlalchemy.create_engine('mysql+pymysql://root:123456@localhost:3306/MyProxies?charset=utf8', echo=False) 
        # 现在我们已经准备好和数据库开始会话了。ORM通过Session与数据库通信的。当应用第一次载入时，我们定义一个Session类
        Session = sqlalchemy.orm.sessionmaker(bind= self.engine)
        # 如果需要和数据库通信，只需要实例化一个Session：
        self.session = Session()

    #元数据是一堆包含的可以在数据库里执行的命令集。因为我们的MySQL数据库目前还没有一个IpProxies表，我们可以使用这些元数据来创建这些表。 
    def initDb(self):
        '''
        在数据库中新建数据库表
        '''
        # 在数据库 MyProxies中新建了一个数据库表 IpProxies
        BaseModel.metadata.create_all(self.engine)

    def dropDb(self):
        '''
        在数据库中删除数据库表
        '''
        BaseModel.metadata.drop_all(self.engine)

    def insert(self, value):
        '''
        向数据库中添加一组数据
        values：待添加IP组，如 [{'ip': '13.187.27.175', 'port': 8080}，{'ip': '192.168.1.1', 'port': 80}]
        '''
        newProxy = IpProxies(ip= value['ip'], port= value['port'], types= value['types'], protocol= value['protocol'],
                            country= value['country'], area= value['area'], updatetime = value['updatetime'],
                            speed= value['speed'], score= value['score'])
        self.session.add(newProxy)
        self.session.commit()
        self.session.close()

    def delete(self, conditions= None):
        '''
        删除满足筛选条件的数据
        conditions：筛选条件，用一个dict传入，如 {'ip': '13.187.27.175', 'port': 8080}
        '''
        if conditions:
            conditionList = []
            for key in list(conditions.keys()):
                if self.params.get(key, None):
                    conditionList.append(self.params.get(key) == conditions.get(key))
            # 通过Session的query()方法创建一个查询对象的IpProxies实例(相当于在IpProxies范围中查找) 。
            query = self.session.query(IpProxies)
            # Query对象是完全可繁殖的（fully generative），意味着大多数方法的调用都返回一个新的Query对象,此对象仍可进行查询操作
            for condition in conditionList:
                query = query.filter(condition)
            #delete()会将其影响的行数作为返回值返回,update()也类似 
            deleteNum = query.delete()
            self.session.commit()
            self.session.close()
        else:
            deleteNum = 0
        return ('deleteNum', deleteNum)

    def update(self, conditions= None, value= None):
        '''
        修改满足筛选条件的数据
        conditions：筛选条件，用一个dict传入，如 {'ip': '13.187.27.175', 'port': 8080}
        value：更新值，用一个dict传入，如 {'port': 9999}
        '''
        if conditions:
            conditionList = []
            valueList = {}
            for key in conditions.keys():
                if self.params.get(key,None):
                    # 构建query.filter()函数的传入值,形如 query.filter(User.name == 'ed') 
                    conditionList.append(self.params.get(key) == conditions.get(key))
            for key in value.keys():
                if self.params.get(key,None):
                    # valueList[key] = value[key] 貌似也没错
                    valueList[self.params.get(key,None)] = value[key]
            query = self.session.query(IpProxies)
            for condition in conditionList:
                query = query.filter(condition)
            updateNum = query.update(valueList)
            self.session.commit()
            self.session.close()
        else:
            updateNum = 0
        return ('upadteNum', updateNum)

    def select(self, conditions= None, count= None):
        '''
        取出满足筛选条件数据
        conditions：筛选条件，用一个dict传入，如 {'ip': '13.187.27.175', 'port': 8080}
        count： 表示需要选择的数据个数
        '''
        conditionList = []
        if conditions:
            for key in conditions.keys():
                if self.params.get(key, None):
                    conditionList.append(self.params.get(key) == conditions.get(key))

        query = self.session.query(IpProxies)

        if len(conditionList)> 0 and count:
            for condition in conditionList:
                query = query.filter(condition)
            # 将筛选出的数据先按score的值降序排列，score值相同的按speed值升序排列（ASC：升序  DESC：降序）
            # all()返回的是一个list, list中的每个元素的类型为：<class '__main__.IpProxies'>
            return query.order_by(IpProxies.score.desc(), IpProxies.speed).limit(count).all()
        elif count:
            return query.order_by(IpProxies.score.desc(), IpProxies.speed).limit(count).all()
        elif len(conditionList)> 0:
            for condition in conditionList:
                query = query.filter(condition)
            return query.order_by(IpProxies.score.desc(), IpProxies.speed).all()
        else:
            return qurey.order_by(IpProxies.score.desc(), IpProxies.speed).all()

if __name__ == '__main__':
    sqlManage = MySQLManager()
    # sqlManage.initDb()
    # sqlManage.dropDb()
    proxy = {'ip': '13.187.27.175', 'port': 8080, 'types': 1, 'protocol': 0, 'country': '中国', 'area': '上海', 'updatetime': 20170301, 'speed': 12.3, 'score': 0}
    # sqlManage.insert(proxy)
    conditions ={'ip': '13.187.27.175', 'port': 8080}
    value = {'port': 9999}
    c = sqlManage.select(conditions)
    print(type(c))
    for i in c:
        print(type(i))
    # print(sqlManage.update(conditions, value))
    # sqlManage.getAll()
