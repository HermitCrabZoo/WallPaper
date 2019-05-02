#!/usr/bin/env python
#coding=utf-8
import urllib.request as request
import sys,os
import datetime
import re
import multiprocessing
import socket

#主页url
homeUrl="https://alpha.wallhaven.cc"
#登录url
loginUrl=homeUrl+"/auth/login"
userName=None
password=None
_token=None
data={"username":userName,"password":password,"_token":_token}
#会话
session=None
#图片列表url
searchUrl=homeUrl+"/search?categories=111&purity=111&resolutions=3840x2160&sorting=views&order=desc&page="
#分辨率
resolutions=["3840x2160","2560x1440","1920x1080"]
#类别条件'普通','动漫','人物'可叠加
categories=["100","010","001"]
#内容类型'科幻','素描','重口'可叠加
puritys=["100","010","001"]
#排序字段'随机','相关性','日期','浏览量','喜好'
sortings=["random","relevance","dateAdded","views","favorites"]
#排序'降序','升序'
orders=["desc","asc"]
#图片下载到本地的目录
destination = "G:\\pic\\"
#下载的图片个数
count = 20
#查询条件-页码
page = 1
#并行的进程数
parallel=1
#下载超时
second=120.0
#超时的次数(最多)
expire=5
#设置全局的下载超时
socket.setdefaulttimeout(second)
#日期格式
timeFormat="%Y-%m-%d %H:%M:%S"


def logging(msg=""):
    print(datetime.datetime.now().strftime(timeFormat)+" "+msg)

def getRequest(url=""):
    req=request.Request(url)
    req.add_header("User-agent", "Mozilla 5.10")
    return req

#判断list中若有一项以上未成功下载，返回true，否则返回false
def needDownload(downloadItems=[]):
    print(downloadItems)
    if downloadItems!=None:
        for item in downloadItems:
            if item[1]==False:
                return True
    return False

#下载图片到本地
def download(item=[],queue=None):
    robReq=getRequest(item[0])
    try:
        robConn=request.urlopen(robReq)
        fileName=robReq.get_full_url().split("/")[-1]
        filePath=destination+fileName
        #文件不存在或文件小于1kB则下载,否则不下载
        if not os.path.exists(filePath) or (os.path.getsize(filePath)/1024)<1:
            logging((robReq.get_full_url().ljust(69," ")+"downloading".ljust(17," ")).ljust(100,"-")+"> ["+("-"*30)+"]")
            with open(destination+fileName,"wb") as file:
                file.write(robConn.read())#写入到文件
                logging((robReq.get_full_url().ljust(69," ")+"download succeed".ljust(17," ")).ljust(100,"-")+"> ["+("#"*30)+"]")
        else:
            logging((robReq.get_full_url().ljust(69," ")+"already exists".ljust(17," ")).ljust(100,"-")+"> ["+("#"*30)+"]")
        item[1]=True
    except Exception as e:
        logging((robReq.get_full_url().ljust(69," ")+"download failed".ljust(17," ")).ljust(100,"-")+"> ["+str(e)+"]")
    queue.put(item)

#启动进程池进行下载
def rob(downloadItems=[]):
    logging("Robbing...")
    downloadCount=1#下载次数
    #重复下载次数未超过限定此时,并且有未完成的下载任务
    while downloadCount<=expire and needDownload(downloadItems):
        logging(str(downloadCount)+" downloads,"+str(len(downloadItems))+" missions")
        items=[]
        downloadCount+=1
        #创建进程池、队列
        manager=multiprocessing.Manager()
        queue=manager.Queue()
        pool = multiprocessing.Pool(processes=parallel)
        for item in downloadItems:
            pool.apply_async(download, (item,queue))#开启进程
        pool.close()
        pool.join()
        while not queue.empty():
            item=queue.get()
            if item[1]==False:#若为False代表此url对应的资源未成功下载,则需要下载
                items.append(item)
        downloadItems=items
    if len(downloadItems)>0:#还有未成功下载的url,表示下载未完成
        logging("Download UNcomplete!")
    elif downloadCount>1:#没有未成功下载的url,但是下载的次数大于1,表示下载完成
        logging("Download completed.")
    else:#没有未成功下载的url,下载次数也不大于1,表示从未下载过
        logging("No download-urls!")

#通过显示图片的url来获取图片的下载url
def addressing(showUrls=[]):
    logging("Addressing...")
    items=[]
    for i,showUrl in enumerate(showUrls[:count]):
        logging("URL-"+str(i)+" : "+showUrl)
        showReq=getRequest(showUrl)
        try:
            showConn=request.urlopen(showReq)
            logging("Reading download url in show connection...")
            resultData=str(showConn.read(),encoding = "utf-8")
            img=re.search("<img id=\"wallpaper\" src=\"(//wallpapers.wallhaven.cc/wallpapers/full/wallhaven-[0-9]+\.[a-zA-Z]+)\"[\s\S]+/>", resultData)
            if img:
                items.append(["https:"+img.group(1),False])
            else:
                logging("Img has not matched in show connection!")
        except Exception as e:
            logging("Addressing failed:"+showReq.get_full_url()+" "+str(e))
    return items

#获取用来显示图片的url的list
def peep(peepUrl=""):
    showUrls=[]
    peepCount=1
    #重复连接次数未超过限定次数,并且未获取到显示图片的url
    while peepCount<=expire and len(showUrls)<1:
        peepCount+=1
        try:
            peepReq=getRequest(peepUrl)
            logging("Peeping...")
            peepConn=request.urlopen(peepReq)
            logging("Peep code:"+str(peepConn.getcode()))
            logging("Reading...")
            resultData=str(peepConn.read(),encoding = "utf-8")
            logging("Matching section...")
            section=re.search("<section class=\"thumb-listing-page\">[\s\S]*</section>", resultData)
            if section:
                logging("Matching images...")
                aTags=re.findall("<a class=\"preview\" href=\"(https:\/\/alpha.wallhaven.cc\/wallpaper\/[0-9]+)\" +target=\"_blank\" *></a>", section.group())
                if aTags:
                    logging("Images has matched.")
                    showUrls=aTags
                else:
                    logging("Images has not matched in section!")
            else:
                logging("Section has  not matched in peep url!")
        except Exception as e:
            logging("Peep has exception!")
            logging(peepReq.get_full_url()+" "+str(e))
    if len(showUrls)<1:
        logging("Peeping failed! I have tried it "+str(expire)+" times.")
    return showUrls

#控制中心
def control():
    global count,page
    argError="Invalid parameter:"
    ruleHint="""Usage:[count|] [page|]
parameter can be:
    count:number of pictures to download
    page:condition of search 
    """
    args=sys.argv
    if len(args)>1:
        if not args[1].isdigit() or int(args[1])<=0:
            print(argError+"'"+args[1]+"' Must be an Integer greater than zero!")
            print(ruleHint)
            return
        count=int(args[1])
        if len(args)>2:
            if not args[2].isdigit() or int(args[2])<=0:
                print(argError+"'"+args[2]+"' Must be an Integer greater than zero!")
                print(ruleHint)
                return
            page=int(args[2])
    logging("Grabber started.")
    logging("loginUrl:"+loginUrl)
    #logging("userName:"+userName)
    #logging("password:"+password)
    logging("searchUrl:"+searchUrl)
    #logging("robUrl:"+robUrl)
    logging("count:"+str(count)+",page:"+str(page)+",timeout:"+str(second)+"s"+",expire:"+str(expire))
    #掠夺图片到本地
    for i in range(0,page+1):
        logging("round "+str(i))
        rob(downloadItems=addressing(showUrls=peep(peepUrl=searchUrl+str(i))))
    
    

#程序入口
if __name__=="__main__":
    control()
