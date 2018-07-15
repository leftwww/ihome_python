# -- coding: utf-8 --
# @Author : zw
# @File : config.py
import redis


class Config(object):
    """工程的配置信息"""
    SECRET_KEY = "-0s9djgopsdngjsd-gsdf0-as"

    # 数据库的配置信息 mysql
    SQLALCHEMY_DATABASE_URI = "mysql://root:mysql@127.0.0.1:3306/ihome_python"
    # SQLALCHEMY_DATABASE_URI = "mysql://root:mysql@127.0.0.1:3306/ihome_python02
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    # redis
    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = 6379

    # flask_session用到的配置信息
    SESSION_TYPE = "redis"  # 指明保存到redis中
    SESSION_USE_SINGER = True  # 让cookie中session_id被加密签名处理
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST,port=REDIS_PORT)
    PERMANENT_SESSION_LIFETIME = 86400 # 配置session的有效期，单位秒


class DevelopmentConfig(Config):
    """开发模式使用的配置信息"""
    DEBUG = True


class ProductionConfig(Config):
    """生产模式 线上模式的配置信息"""
    pass


config_dict = {
    "develop":DevelopmentConfig,
    "product":ProductionConfig,
}
#
# d = {'a':24,'g':52,'i':12,'k':33}
# print sorted(d.items(),key = lambda x:x[1])
#
# print('aStr'[::-1])
# str1 = "k:1|k1:2|k2:3|k3:4"
# def str2dict(str1):
#     dict1 = {}
#     for iterms in str1.split('|'):
#         key,value = iterms.split(':')
#         dict1[key] = value
#         # print dict1
#     return dict1
# s = str2dict(str1)
# print s