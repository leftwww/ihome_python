# -- coding: utf-8 -- 
# @Author : zw
# @File : __init__.py.py

from flask import Blueprint

# 创建蓝图对象
api = Blueprint("api_1_0", __name__)


from . import index,orders,verify_code,houses,passport,profile
