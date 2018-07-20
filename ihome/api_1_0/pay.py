# -- coding: utf-8 -- 
# @Author : zw
# @File : pay.py


from  . import api
from ihome.utils.commons import login_required
from ihome.models import Order
from flask import g,current_app,jsonify
from ihome.utils.response_code import RET

@api.route("/orders/<int:order_id>/payment",methods=["POST"])
@login_required
def generate_order_payment(order_id):
    """生成支付宝的支付信息"""
    user_id = g.user_id
    # 校验参数
    try:
        order = Order.query.filter(Order.id == order_id, Order.user_id == user_id,Order.status == "WAIT_PATMENT").first()
    except Exception as e:
        current_app.logger.error(e)
