# -*- coding: utf-8 -*-
import logging
import sys

LOGS = {}


def get(name):
    """获取Logger对象，指定对象name"""
    if name in LOGS:
        return LOGS.get(name)
    # 获取logger实例，如果参数为空则返回root logger
    logger = logging.getLogger(name)
    # 指定日志的最低输出级别，默认为WARN级别
    logger.setLevel(logging.INFO)
    logger.propagate = 0
    # 指定logger输出格式
    formatter = logging.Formatter('%(asctime)s %(process)d:%(threadName)s %(levelname)-4s: %(message)s')
    # 控制台日志
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.formatter = formatter  # 也可以直接给formatter赋值
    console_handler.setLevel(logging.INFO)
    # 为logger添加的日志处理器，可以自定义日志处理器让其输出到其他地方
    logger.addHandler(console_handler)
    LOGS[name] = logger
    return logger


def root():
    return get("root")


