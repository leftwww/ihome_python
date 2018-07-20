# # -- coding: utf-8 --
# # @Author : zw
# # @File : houses.py
#
from . import api
from ihome.models import Area
from flask import current_app,jsonify,g,request,session
from ihome.utils.response_code import RET
from ihome import redis_store,constants,db
import json
from ihome.utils.commons import login_required
from ihome.models import House,Facility,HouseImage,User,Order
from ihome.utils.image_storage import storage
from datetime import datetime


@api.route("/areas")
def get_area_info():
    """获取城区信息"""
    # 先尝试从redis中获取缓存数据
    try:
        areas_json = redis_store.get("area_info")
    except Exception as e:
        current_app.logger.error(e)
    if areas_json is None:
        # 查询数据库，获取城区信息
        try:
            areas_list = Area.query.all()
        except Exception as e:
            current_app.logger.error(e)

            return jsonify(errno=RET.DBERR,errmsg="查询城区信息异常")

        # 遍历列表，处理每一个对象，转换一下对象的属性名
        areas = []
        for area in areas_list:
            areas.append(area.to_dict())

        # 将数据转换为json
        areas_json = json.dumps(areas)
        # 将数据在redis中保存一份缓存
        try:
            redis_store.setex("area_info",constants.AREA_INFO_REDIS_EXPIRES,areas_json)
        except Exception as e:
            current_app.logger.error(e)

    else:
        # 表示redis中有缓存，直接使用的是缓存数据
        current_app.logger.info("shuai")

    # 从redis中去取json数据或者从数据库中查询并转为json数据
    # areas_json = '[{"aid":xx,"aname":xxx},{},{}]'

    # return jsonify(errno=RET.OK, errmsg="查询城区信息成功",data={"areas":areas})
    return '{"errno":0,"errmsg":"查询城区信息成功","data":{"areas":%s}}' % areas_json,200,\
           {"Content-Type":"application/json"}


@api.route("/houses/info",methods=["POST"])
@login_required
def save_house_info():
    """保存房屋的基本信息"""
    # 获取参数
    house_data = request.get_json()
    if house_data is None:
        return jsonify(errno=RET.PARAMERR,errmsg="参数错误")

    title = house_data.get("title") # 标题
    price = house_data.get("price")  # 单价，单位：分
    area_id= house_data.get("area_id")
    address = house_data.get("address")  # 地址
    room_count = house_data.get("room_count")  # 房间数目
    acreage = house_data.get("acreage") # 房屋面积
    unit = house_data.get("unit") # 房屋单元， 如几室几厅
    capacity = house_data.get("capacity")  # 房屋容纳的人数
    beds = house_data.get("beds")  # 房屋床铺的配置
    deposit = house_data.get("deposit")  # 房屋押金
    min_days = house_data.get("min_days")  # 最少入住天数
    max_days = house_data.get("max_days")  # 最多入住天数，0表示不限制


    # 校验参数
    if not all([max_days,min_days,
                deposit,beds,capacity,unit,acreage,
                room_count,address,price,title]):
        return jsonify(errno=RET.PARAMERR,errmsg="参数不完整")

    # 判断单价和押金格式是否正确
    # 前端传送过来的金额参数是已元为单位，浮点数，数据库中保存的是以分为单位
    try:
        price = int(float(price)) * 100
        deposit = int(float(deposit)) * 100
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg="参数有误")


    # 保存信息
    user_id = g.user_id
    house = House(
        user_id = user_id,
        area_id = area_id,
        title = title,
        max_days = max_days,
        min_days = min_days,
        deposit =deposit,
        beds= beds,
        capacity =capacity,
        unit = unit,
        acreage =acreage,
        room_count =room_count,
        address =address,
        price =price
    )
    # 处理房屋的设施信息
    facility_id_list = house_data.get("facility")

    if facility_id_list:
        # 表示用户勾选了房屋设施
        # 过滤用户传送的不合理设施id
        try:
            facility_list = Facility.query.filter(Facility.id.in_(facility_id_list)).all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="数据库异常")

        # 为房屋添加设施信息
        if facility_list:
            house.facilities = facility_list

    try:
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存数据失败")

    # 返回值
    return jsonify(errno=RET.OK, errmsg="保存成功",data={'house_id':house.id})


@api.route("/houses/image",methods=["POST"])
@login_required
def save_house_image():
    """保存房屋的图片"""
    # 获取参数 房屋的图片 房屋编号
    house_id = request.form.get("house_id")
    image_file = request.files.get("house_image")

    # 校验参数
    if not all([house_id,image_file]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    # 判断房屋是否存在
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")

    if house is None:
        return jsonify(errno=RET.NODATA, errmsg="房屋不存在")

    # 上传房屋图片到七牛中
    image_data = image_file.read()
    try:
        file_name = storage(image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="保存房屋图片失败")

    # 保存图片信息到数据库中
    house_image = HouseImage(
        house_id = house_id,
        url = file_name,
    )
    db.session.add(house_image)

    # 处理房屋基本信息中的主图片
    if not house.index_image_url:
        house.index_image_url = file_name
        db.session.add(house)
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存图片信息失败")

    image_url = constants.QINIU_URL_DOMAIN+file_name
    return jsonify(errno = RET.OK,errmsg="保存图片成功",data = {"image_url":image_url})


@api.route("/user/houses",methods=["GET"])
@login_required
def get_user_huoses():
    """获取房东发布的房源信息条目"""
    user_id = g.user_id

    try:
        houses = House.query.filter_by(user_id=user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="获取数据失败")

    # 将查询的房屋信息转换为字典存放到列表中
    houses_list = []
    if houses:
        for house in houses:
            houses_list.append(house.to_basic_dict())
    return jsonify(errno=RET.OK,errmsg="OK",data={"houses":houses_list})

@api.route("/houses/index",methods=["GET"])
def get_house_index():
    """获取主页幻灯片展示的房屋基本信息"""
    # 从缓存中尝试获取数据
    # print 1111111111111111111111111111111111
    try:
        ret = redis_store.get("home_page_data")
    except Exception as e:
        current_app.logger.error(e)
        ret = None
    if ret:
        current_app.logger.info("hit house index info redis")
        # 因为redis中保存的是json字符串，所以直接进行字符串拼接返回
        return '{"errno":0, "errmsg":"OK", "data":%s}' % ret, 200, {"Content-Type": "application/json"}
    else:
        try:
            # 查询数据库，返回房屋订单数目最多的5条数据
            houses = House.query.order_by(House.order_count.desc()).limit(constants.HOME_PAGE_MAX_HOUSES)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="查询数据失败")

        if not houses:
            return jsonify(errno=RET.NODATA, errmsg="查询无数据")

        houses_list = []
        for house in houses:
            # 如果房屋未设置主图片，则跳过
            if not house.index_image_url:
                continue
            houses_list.append(house.to_basic_dict())

        # 将数据转换为json，并保存到redis缓存
        json_houses = json.dumps(houses_list)
        try:
            redis_store.setex("home_page_data", constants.HOME_PAGE_DATA_REDIS_EXPIRES, json_houses)
        except Exception as e:
            current_app.logger.error(e)

        return '{"errno":0, "errmsg":"OK", "data":%s}' % json_houses, 200, {"Content-Type": "application/json"}


@api.route("/houses/<int:house_id>",methods=["GET"])
def get_house_detail(house_id):
    """获取房屋详情"""
    # 前端在房屋详情页面展示时，如果浏览器页面的用户不是该房屋的房东，则展示预定按钮，否则不展示
    # 所以需要后端返回登录用户的user_id
    # 尝试获取用户登陆的信息，若登陆，则返回给前端登录用户的user_id，否则返回user_id=-1
    user_id = session.get("user_id", "-1")

    # 校验参数
    if not house_id:
        return jsonify(errno=RET.PARAMERR, errmsg="参数确实")

    # 先从redis缓存中获取信息
    try:
        ret = redis_store.get("house_info_%s" % house_id)
    except Exception as e:
        current_app.logger.error(e)
        ret = None
    if ret:
        current_app.logger.info("hit house info redis")
        return '{"errno":"0", "errmsg":"OK1111", "data":{"user_id":%s, "house":%s}}' % (user_id, ret), 200, {
            "Content-Type": "application/json"}

    # 查询数据库
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据失败")

    if not house:
        return jsonify(errno=RET.NODATA, errmsg="房屋不存在")

    # 将房屋对象数据转换为字典
    try:
        house_data = house.to_full_dict()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg="数据出错")

    # 存放到redis中
    json_house = json.dumps(house_data)
    # print json_house
    # print 11111111
    try:
        redis_store.setex("house_info_%s" % house_id, constants.HOUSE_DETAIL_REDIS_EXPIRE_SECONE, json_house)
    except Exception as e:
        current_app.logger.error(e)

    resp = '{"errno":"0", "errmsg":"OK", "data":{"user_id":%s, "house":%s}}' % (user_id, json_house), 200, {
        "Content-Type": "application/json"}
    return resp


# /api/v1_0/houses?sd=xxxx-xx-xx&ed=xxxx-xx-xx&aid=xx&sk=new&p=1
@api.route("/houses", methods=["GET"])
def get_house_list():
    """获取房屋列表信息"""
    # 获取参数
    start_date_str = request.args.get("sd", "")  # 想要查询的起始时间
    end_date_str = request.args.get("ed", "")  # 想要查询的终止时间
    area_id = request.args.get("aid", "")  # 区域id
    sort_key = request.args.get("sk", "new2")  # 排序关键字
    page = request.args.get("p", 1)  # 页数

    # 校验参数
    # 判断日期
    try:
        start_date = None
        if start_date_str:
            start_date = datetime.strptime(start_date_str,"%Y-%m-%d")

        end_date = None
        if end_date_str:
            end_date = datetime.strptime(start_date_str, "%Y-%m-%d")

        # 判断起始时间和终止时间是否为空
        if start_date and end_date:
            # 断言起始时间大于等于终止时间 否则报错，下面捕获
            assert start_date <= end_date
    except Exception as e:
        return jsonify(errno = RET.PARAMERR,errmsg="日期参数有误")

    # 判断页数
    try:
        page = int(page)
    except Exception:
        page = 1

    # 先从redis缓存中获取数据
    try:
        redis_key = "house_%s_%s_%s_%s" % (start_date_str, sort_key, area_id, end_date_str)
        resp_json = redis_store.hget(redis_key,page)
    except Exception as e:
        current_app.logger.error(e)
        resp_json = None

    if resp_json:
        # 表示从缓存中拿到了数据
        return resp_json, 200, {"Content-Type": "application/json"}

    # 查询数据
    filter_params = []

    # 处理区域信息
    if area_id:
        filter_params.append(House.area_id == area_id)
    try:
        # 处理时间
        conflict_orders_li = []
        if start_date and end_date:
            # 从订单表中查询 冲突 的订单，进而获取冲突的房屋id
            conflict_orders_li = Order.query.filter(Order.begin_date <= end_date,Order.end_date >= start_date).all()

        elif start_date:
            # 从订单表中查询 冲突 的订单，进而获取冲突的房屋id
            conflict_orders_li = Order.query.filter(Order.end_date >= start_date).all()

        elif end_date:
            # 从订单表中查询 冲突 的订单，进而获取冲突的房屋id
            conflict_orders_li = Order.query.filter(Order.begin_date <= end_date).all()

    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="数据库异常")

    if conflict_orders_li:
        conflict_house_id_li = [order.house_id for order in conflict_orders_li]
        # 添加条件，查询不冲突的房屋      notin_取反     in_取正
        filter_params.append(House.id.notin_(conflict_house_id_li)).all()

    # 排序
    if sort_key == "booking":
        House_query = House.query.filter(*filter_params).order_by(House.order_count.desc())
    elif sort_key == "price-inc":
        House_query = House.query.filter(*filter_params).order_by(House.price.asc())
    elif sort_key == "price-des":
        House_query = House.query.filter(*filter_params).order_by(House.price.desc())
    else:
        House_query = House.query.filter(*filter_params).order_by(House.create_time.desc())

    # 分页 sqlalchemy的分页
    try:
        #                                 页数      每页数量                        错误输出
        house_page = House_query.paginate(page,constants.HOUSE_LIST_PAGE_CAPACITY,False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno = RET.DBERR,errmsg="数据库异常")

    house_li = house_page.items  # 当前页中的数据结果
    total_page = house_page.pages  # 总页数

    houses=[]
    for house in house_li:
        houses.append(house.to_basic_dict())

    # 将结果转换为json字符串
    resp = dict(errno=RET.OK, errmsg="查询成功", data={"houses": houses, "total_page": total_page, "current_page": page})
    resp_json = json.dumps(resp)
    # 设置缓存数据存到redis中
    if page <= total_page:
        # 用redis的哈希类型保存分页数据
        redis_key = "houses_%s_%s_%s_%s" % (start_date_str, end_date_str, area_id, sort_key)
        try:
            # 使用redis中的事务
            # 创建事物
            pipeline = redis_store.pipeline()
            # 开启事务
            pipeline.multi()
            pipeline.hset(redis_key, page, resp_json)
            pipeline.expire(redis_key, constants.HOUSE_LIST_PAGE_REDIS_EXPIRES)
            # 执行事务
            pipeline.execute()
        except Exception as e:
            current_app.logger.error(e)

    # 返回
    return resp_json, 200, {"Content-Type": "application/json"}

