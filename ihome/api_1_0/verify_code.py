# -- coding: utf-8 -- 
# @Author : zw
# @File : verify_code.py

from . import api
from ihome import redis_store,constants
from ihome.utils.captcha.captcha import captcha
from flask import current_app,jsonify,request,make_response
from ihome.utils.response_code import RET
import random
from ihome.constants import SMS_CODE_REDIS_EXPIRES
from libs.yuntongxun.sms import CCP
# from ihome.tasks.task_sms import send_template_sms
from ihome.tasks.sms import tasks


# url:/api/v1_0/image_codes/<image_code_id>
# methods:get
# 传入参数：
# 返回值：正常情况返回->图片,异常->json

@api.route("/image_codes/<image_code_id>")
def get_image_code(image_code_id):
    """提供图片验证码"""
    # 业务处理
    # 生成验证码图片
    # 名字，验证码真实值，图片的二进制内容
    name,text,image_data = captcha.generate_captcha()

    try:
        # 保存验证码的真实值与编号
        # redis_store.set('image_code_%s' % image_code_id,text)
        # redis_store.expires('image_code_%s' % image_code_id)
        # 生成键的同时生成有效期
        redis_store.setex('image_code_%s' % image_code_id,constants.IMAGE_CODE_REDIS_EXPIRES,text)
    except Exception as e:
        # 在日志中记录异常
        current_app.logger.erroe(e)
        resp={
            "error":RET.DBERR,
            # "error":"save image code failed",
            "errmsg":"Failed to save the verification code"
        }
        return jsonify(resp)

    # 返回验证码图片
    resp =make_response(image_data)
    resp.headers["Content-Type"] = "image/jpg"
    return resp


# GET /api/v1_0/sms_codes/<mobile>?image_code_id=xx&image_code=xxx
# 用户填写的图片验证码
# 图片验证码的编码
# 用户的手机号码

# @api.route("/sms_codes/<re(r'1[345789]\d{9}'):mobile>")
# def send_sms_code(mobile):
#     """发送短信验证码"""
#     # 获取参数
#     image_code_id = request.args.get("image_code_id")
#     image_code = request.args.get("image_code")
#
#     # 校验参数
#     if not all([image_code_id,image_code]):
#         resp = {
#             "errno":RET.PARAMERR,
#             "errmsg":"参数不完整"
#         }
#         return jsonify(resp)
#
#     # 判断
#
#     # 业务逻辑
#     # 1 取出真实的图片验证码
#     try:
#         real_image_code = redis_store.get("image_code_%s"% image_code_id)
#     except Exception as e:
#         current_app.logger.error(e)
#         resp = {
#             "errno":RET.DBERR,
#             "errmsg":"获取图片的验证码失败"
#         }
#         return jsonify(resp)
#
#     # 2 判断验证码的有效期
#     if real_image_code is None:
#         # 表示redis中没有这个数据
#         resp = {
#             "errno": RET.NODATA,
#             "errmsg": "图片验证码过期"
#         }
#         return jsonify(resp)
#
#     # 删除redis中的图片验证码，防止用户多次尝试同一个图片验证码
#     try:
#         redis_store.delete("image_code_%s" % image_code_id)
#     except Exception as e:
#         current_app.logger.error(e)
#
#     # 3 判断用户填写的验证码与真实的验证码
#     if real_image_code.lower() != image_code.lower():
#         # 表示用户填写错误
#         resp = {
#             "errno": RET.DATAERR,
#             "errmsg": "图片验证码有误"
#         }
#         return jsonify(resp)
#     # 4 创建短信验证码
#     sms_code = "%06d" % random.randint(0,999999)
#
#     # 5 保存短信验证码
#     try:
#         redis_store.setex("sms_code_%s" % mobile,SMS_CODE_REDIS_EXPIRES,sms_code)
#     except Exception as e:
#         current_app.logger.error(e)
#         resp = {
#             "errno": RET.DBERR,
#             "errmsg": "保存短信验证码异常"
#         }
#         return jsonify(resp)
#     # 6 发送验证码短信
#     try:
#         ccp = CCP()
#         result = ccp.send_template_sms(mobile,[sms_code,str(SMS_CODE_REDIS_EXPIRES/60)],1)
#     except Exception as e:
#         current_app.logger.error(e)
#         resp = {
#             "errno": RET.THIRDERR,
#             "errmsg": "发送短信异常"
#         }
#         return jsonify(resp)
#     if result == 0:
#         resp = {
#             "errno": RET.OK,
#             "errmsg": "发送短信成功"
#         }
#         return jsonify(resp)
#     else:
#         resp = {
#             "errno": RET.THIRDERR,
#             "errmsg": "发送短信失败"
#         }
#         return jsonify(resp)
#     # 返回值


@api.route("/sms_codes/<re(r'1[345789]\d{9}'):mobile>")
def send_sms_code(mobile):
    """发送短信验证码"""
    # 获取参数
    image_code_id = request.args.get("image_code_id")
    image_code = request.args.get("image_code")

    # 校验参数
    if not all([image_code_id,image_code]):
        resp = {
            "errno":RET.PARAMERR,
            "errmsg":"参数不完整"
        }
        return jsonify(resp)

    # 判断

    # 业务逻辑
    # 1 取出真实的图片验证码
    try:
        real_image_code = redis_store.get("image_code_%s"% image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        resp = {
            "errno":RET.DBERR,
            "errmsg":"获取图片的验证码失败"
        }
        return jsonify(resp)

    # 2 判断验证码的有效期
    if real_image_code is None:
        # 表示redis中没有这个数据
        resp = {
            "errno": RET.NODATA,
            "errmsg": "图片验证码过期"
        }
        return jsonify(resp)

    # 删除redis中的图片验证码，防止用户多次尝试同一个图片验证码
    try:
        redis_store.delete("image_code_%s" % image_code_id)
    except Exception as e:
        current_app.logger.error(e)

    # 3 判断用户填写的验证码与真实的验证码
    if real_image_code.lower() != image_code.lower():
        # 表示用户填写错误
        resp = {
            "errno": RET.DATAERR,
            "errmsg": "图片验证码有误"
        }
        return jsonify(resp)
    # 4 创建短信验证码
    sms_code = "%06d" % random.randint(0,999999)

    # 5 保存短信验证码
    try:
        redis_store.setex("sms_code_%s" % mobile,SMS_CODE_REDIS_EXPIRES,sms_code)
    except Exception as e:
        current_app.logger.error(e)
        resp = {
            "errno": RET.DBERR,
            "errmsg": "保存短信验证码异常"
        }
        return jsonify(resp)

    # 使用celery发送验证码短信
    # tasks.send_template_sms.delay(mobile,[sms_code,str(constants.SMS_CODE_REDIS_EXPIRES/60)],1)

    result = tasks.send_template_sms.delay(mobile,[sms_code,str(constants.SMS_CODE_REDIS_EXPIRES/60)],1)
    # 返回异步结果对象，通过这个对象能够获取最终执行的结果
    print result.id
    # 通过get方法能不用自己去backend中拿取执行结果，get方法会帮助问哦们返回执行结果
    # get()默认是阻塞的，会等到worker执行完成了结果的时候才会返回
    # get()通过timeout超时时间，可以在超过超时时间后立即返回
    ret = result.get()
    print ret

    return jsonify(errno=RET.OK,errmsg="OK")




