# -- coding: utf-8 -- 
# @Author : zw
# @File : config.py

from celery import Celery
from ihome.tasks import config

BROKER_URL = "redis://127.0.0.1:6379/5"
CELERY_RESULT_BACKEND = "redis://127.0.0.1:6379/6"