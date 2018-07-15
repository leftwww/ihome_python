# -- coding: utf-8 -- 
# @Author : zw
# @File : index.py

from . import api

from ihome import db,models  # 将models导入进来，让框架知道有了这个文件，
                            # 这样在生成迁移文件的时候就不会，报没有变化了
import logging
from flask import current_app


@api.route('/index')
def hello_world():
    # 是一个函数，类似与print
    # logging.error("sgewrsdw")  # 错误级别
    # logging.warn("")  # 警告级别
    # logging.info("")  # 信息级别或者叫消息提示级别
    # logging.debug()  # 调试级别
    current_app.logger.error("error msg")
    current_app.logger.warn("warn msg")
    current_app.logger.info("info msg")
    current_app.logger.debug("debug msg")

    return 'Hello World!'