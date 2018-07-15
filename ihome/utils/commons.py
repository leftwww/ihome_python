# -- coding: utf-8 -- 
# @Author : zw
# @File : commons.py

from werkzeug.routing import BaseConverter
from flask import session,jsonify,g
from ihome.utils.response_code import RET

# 自定义的接受正则表达式的路由转换器
class RegexConverter(BaseConverter):

    def __init__(self,url_map,regex):
        """regex是在路由中填写的正则表达式"""
        super(RegexConverter,self).__init__(url_map)
        # super(ReConverter, self).__init__(url_map)
        self.regex = regex


def login_required(view_func):
    """检验用户的登陆状态"""
    def wrapper(*args,**kwargs):
        user_id = session.get("user_id")
        if user_id is not None:
            # 表示用户已经登录
            # 使用g对象保存user_id,在视图 函数中可以直接使用
            g.user_id = user_id
            return view_func(*args,**kwargs)
        else:
            # 用户未登录
            resp = {
                "errno":RET.SESSIONERR,
                "errmsg":"用户未登录"
            }
            return jsonify(resp)
    return wrapper

