# -*- coding: utf-8 -*-
import os
import sys
from argparse import ArgumentParser, ArgumentTypeError
import itertools
from urllib import parse
import Logger
from pyquery import PyQuery as Q
import requests
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import copy


logger = Logger.get("AwesomeWallpaper")


headers = {"Referer": "https://wallhaven.cc/", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36"}

executor = None

# 主页url
home_url = "https://wallhaven.cc"
# 登录url
login_url = home_url + "/auth/login"
# 会话
session = requests.session()
session.headers.update(headers)
# 图片下载到本地的目录
destination = ""
# 下载超时
timeout = 120.0
# 超时的次数(最多)
times = 5
# 下载间隔
interval = 0


def download(url):
    """下载图片到本地"""
    try:
        file_path = os.path.join(destination, url.rsplit("/", 1)[-1])
        # 文件不存在或文件小于1kB则下载,否则不下载
        if not os.path.exists(file_path) or os.path.getsize(file_path) < 1024:
            logger.info("下载：{}".format(url))
            response = session.get(url, stream=True, timeout=timeout)
            with open(file_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
            logger.info("下载成功：{} -> {}".format(url, file_path))
        else:
            logger.info("文件已存在：{}, URL：{}".format(file_path, url))
    except Exception as e:
        logger.info("下载出错：{} {}".format(e, traceback.format_exc()))
        return url
    return None


def rob(urls):
    """启动线程池进行下载"""
    count, downloads = 0, urls
    # 重复下载次数未超过限定此时,并且有未完成的下载任务
    while count < times and downloads:
        count += 1
        logger.info("第{}次下载，{}个任务。".format(count, len(downloads)))
        futures = [executor.submit(download, item) for item in downloads]
        downloads = [future.result() for future in as_completed(futures) if future.result() is not None]
    return len(set(urls) - set(downloads))


def addressing(previews):
    """通过显示图片的url来获取图片的下载url"""
    downloads = []
    for i, url in enumerate(previews):
        try:
            response = session.get(url, timeout=timeout)
            img_url = Q(response.text)("#wallpaper").attr("src")
            if img_url:
                downloads.append(img_url)
            else:
                logger.info("未找到下载图片的url：{}".format(url))
        except Exception as e:
            logger.error("Addressing '{}' has exception：{}".format(url, e))
    return downloads


def peep(page_url):
    """获取用来显示图片的url的list"""
    previews = []
    peep_count, success = 0, False
    # 重复连接次数未超过限定次数,并且未成功获取到显示图片的url
    while not success and peep_count <= times:
        peep_count += 1
        try:
            response = session.get(page_url, timeout=timeout)
            previews = [item.attr("href") for item in Q(response.text)("#thumbs a.preview").items()]
            success = True
        except Exception as e:
            logger.error("Peep '{}' has exception: {}".format(page_url, e))
    if len(previews) < 1:
        logger.warning("Peeping failed! I have tried it " + str(times) + " times.")
    return previews


def do_login(user, password):
    """登录

    :param user: 用户名
    :param password: 密码
    :return: 登录成功返回True
    """
    # 请求一次首页获取token
    response = session.get(home_url, timeout=timeout)
    _token = Q(response.text)("head meta[name='csrf-token']").attr("content")
    data = {"username": user, "password": password, "_token": _token}
    response = session.post(login_url, data=data, timeout=timeout)
    return Q(response.text)("#userpanel").is_(":contains('{}')".format(user))


class AccessiblePath(object):
    """可写目录"""
    def __call__(self, string):
        try:
            if not os.path.exists(string):
                raise Exception("not exists.")
            if not os.path.isdir(string):
                raise Exception("not a dir.")
            if not os.access(string, os.W_OK):
                raise Exception("can't not access.")
            return string
        except Exception as e:
            raise ArgumentTypeError("invalid path value {}: {}".format(string, e))


class Numeric(object):
    """限定大小的数值"""
    def __init__(self, _type, name, limit=0, gte=True):
        self.type = _type
        self.name = name
        self.limit = limit
        self.gte = gte

    def __call__(self, string):
        value = self.type(string)
        if self.gte is True and value < self.limit:
            raise ArgumentTypeError("must be greater than or equal to {}".format(self.limit))
        elif self.gte is not True and value > self.limit:
            raise ArgumentTypeError("must be less than or equal to {}".format(self.limit))
        return value

    def __repr__(self):
        return self.name


class Int(Numeric):
    """限定大小的int值"""
    def __init__(self, limit=0, gte=True):
        super().__init__(int, "int", limit, gte)


class Float(Numeric):
    """限定大小的float值"""
    def __init__(self, limit=0, gte=True):
        super().__init__(float, "float", limit, gte)


def control():
    # 类别条件'普通','动漫','人物'可叠加
    categories = list(map(lambda x: "".join(x), itertools.product(["0", "1"], repeat=3)))
    # 内容类型'科幻','素描','重口'可叠加
    puritys = list(map(lambda x: "".join(x), itertools.product(["0", "1"], repeat=3)))
    # 排序字段'随机','相关性','日期','浏览量','喜好','榜单'
    sortings = ["random", "relevance", "date_added", "views", "favorites", "toplist"]
    # 排序'降序','升序'
    orders = ["desc", "asc"]
    # 分辨率
    resolutions = ["1280x720", "1280x800", "1280x960", "1280x1024", "1600x900", "1600x1000", "1600x1200", "1600x1280", "1920x1080", "1920x1200", "1920x1440",
                   "1920x1536", "2560x1440", "2560x1600", "2560x1920", "2560x2048", "3840x2160", "3840x2400", "3840x2880", "3840x3072"]
    # 并发数
    parallels = list(range(1, os.cpu_count() * 2 + 1))
    parallel_metavar = "{"+",".join(map(str, parallels[:2]+["..."]+parallels[-2:]))+"}" if len(parallels) > 4 else "{"+",".join(map(str, parallels))+"}"

    # 校验参数
    parser = ArgumentParser(description="Awesome Wallpaper提取", epilog="此致，敬礼！")
    parser.add_argument("-d", "--dir", type=AccessiblePath(), dest="dir", metavar="<dir>", help="保存的目录，必选。", required=True)
    parser.add_argument("-m", "--mode", type=str, dest="mode", choices=["search", "random", "toplist", "latest"], help="搜索模式，默认random，仅search、toplist模式支持其他过滤条件。", default="random")
    parser.add_argument("-q", "--query", type=str, dest="query", metavar="<query>", help="搜索关键字，默认空。", default="")
    parser.add_argument("-c", "--category", type=str, dest="category", metavar="{"+",".join(categories)+"}", choices=categories, help="分类：'普通'、'动漫'、'人物'；(1：包含，0：不包含)，可叠加，默认110。", default="111")
    parser.add_argument("-p", "--purity", type=str, dest="purity", metavar="{"+",".join(puritys)+"}", choices=puritys, help="内容风格：'科幻'、'素描'、'重口'；(1：包含，0：不包含)，可叠加，默认110。", default="110")
    parser.add_argument("-s", "--sort", type=str, dest="sort", choices=sortings, help="排序，默认relevance。", default="relevance")
    parser.add_argument("-o", "--order", type=str, dest="order", choices=orders, help="排序规则，默认desc。", default="desc")
    parser.add_argument("-r", "--resolutions", type=str, dest="resolutions", metavar="<resolution>", choices=resolutions, help="分辨率，默认所有(当mode为search、toplist时该参数才有效)。", default=[], nargs="*")
    parser.add_argument("-f", "--from", type=Int(1), dest="from", metavar="<from>", help="起始页，默认1。", default=1)
    parser.add_argument("-t", "--to", type=Int(1), dest="to", metavar="<to>", help="结束页，默认1。", default=1)
    parser.add_argument("-timeout", type=Int(), dest="timeout", metavar="<timeout>", help="下载超时(s)，默认120。", default=120)
    parser.add_argument("-times", type=Int(), dest="times", metavar="<times>", help="下载失败次数，默认5。", default=5)
    parser.add_argument("-parallel", type=Int(1), dest="parallel", metavar=parallel_metavar, choices=parallels, help="并发数,默认1。", default=1)
    parser.add_argument("-limit", type=Int(1), dest="limit", metavar="<limit>", help="限制下载的个数，默认无限个。", default=sys.maxsize)
    parser.add_argument("-user", type=str, dest="user", metavar="<user>", help="用户名。")
    parser.add_argument("-pwd", type=str, dest="pwd", metavar="<pwd>", help="密码。")
    # parser.add_argument("-interval", type=Float(), dest="interval", metavar="interval", help="下载间隔s，默认0。", default=0)
    args = parser.parse_args()
    copied = copy.deepcopy(args)
    if copied.pwd:
        copied.pwd = "***"
    print(copied)

    if args.user and args.pwd:
        if do_login(args.user, args.pwd):
            logger.info("登录成功：{}".format(args.user))
        else:
            logger.warning("登录失败，请检查账户密码！")
            return

    # 初始化全局变量
    global executor, destination, times, timeout, interval
    executor, destination, times, timeout, interval = ThreadPoolExecutor(max_workers=args.parallel), args.dir, args.times, args.timeout, 0

    limit = args.limit
    page = getattr(args, "from")
    params = {"q": args.query, "categories": args.category, "purity": args.purity, "sorting": args.sort, "order": args.order, "resolutions": ",".join(args.resolutions)}
    # 掠夺图片到本地
    count = 0
    start = time.time()
    for i in range(page, args.to + 1):
        if count >= limit:
            break
        params.update(page=i)
        url = "{}/{}?{}".format(home_url, args.mode, parse.urlencode(params))
        logger.info("page {}：{}".format(i, url))
        show_urls = peep(url)
        show_urls = show_urls[:limit - count]
        urls = addressing(show_urls)
        count += rob(urls)
    end = time.time()
    logger.info("下载完成，共{}个，期望{}个，用时：{}s，起始页：{}，终止页：{}，期望起始页：{}，期望终止页：{}。".format(count, limit, (end-start)/1000, page, i, page, args.to))

    
if __name__ == "__main__":
    control()
