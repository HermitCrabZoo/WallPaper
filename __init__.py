# -*- coding: utf-8 -*-


def limit(minimum, value, maximum):
    """
    限制value在minimum和maximum之间

    :param minimum: 最小值
    :param value: 需要被限制的值
    :param maximum: 最大值
    :return:
    """
    if value < minimum:
        return minimum
    if value > maximum:
        return maximum
    return value