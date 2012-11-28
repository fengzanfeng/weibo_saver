#coding=utf8
import os
import urllib
import urllib2
import cookielib
import base64
import re
import json
import hashlib
import thread_pool
import Queue
import json


login_data = {
    'entry': 'weibo',
    'gateway': '1',
    'from': '',
    'savestate': '7',
    'userticket': '1',
    'ssosimplelogin': '1',
    'vsnf': '1',
    'vsnval': '',
    'su': '',
    'service': 'miniblog',
    'servertime': '',
    'nonce': '',
    'pwencode': 'wsse',
    'sp': '',
    'encoding': 'UTF-8',
    'url': 'http://weibo.com/ajaxlogin.php?framelogin=1&callback=parent.sinaSSOController.feedBackUrlCallBack',
    'returntype': 'META'
}

def get_servertime():
    servertime_url = 'http://login.sina.com.cn/sso/prelogin.php?entry=weibo&callback=sinaSSOController.preloginCallBack&su=dW5kZWZpbmVk&client=ssologin.js(v1.3.18)&_=1329806375939'
    data = urllib2.urlopen(servertime_url).read()
    p = re.compile('\((.*)\)')
    try:
        json_data = p.search(data).group(1)
        data = json.loads(json_data)
        servertime = str(data['servertime'])
        nonce = data['nonce']
        return servertime, nonce
    except:
        print 'Get severtime error!'
        return None

def get_pwd(pwd, servertime, nonce):
    pwd1 = hashlib.sha1(pwd).hexdigest()
    pwd2 = hashlib.sha1(pwd1).hexdigest()
    pwd3_ = pwd2 + servertime + nonce
    pwd3 = hashlib.sha1(pwd3_).hexdigest()
    return pwd3

def get_user(username):
    username_ = urllib.quote(username)
    username = base64.encodestring(username_)[:-1]
    return username

def get_follower(user,page):
    req_follow = urllib2.Request(url='http://weibo.com/%d/follow?page=%d' % (user,page),)
    result = urllib2.urlopen(req_follow)
    text = result.read().decode('utf-8')
    follows = re.findall(r"(uid=)([0-9]*)(&fnick=)(\S*)(&sex=[f|m]+)\\\">", text)

    for follow in follows:
        print follow[1]+"\t"+follow[3]

    if page == 1 :
        follow = re.findall(r"(strong node-type.*follow[^>]*>)(\d*)([^>]*strong>)", text)
        follows = follow[0][1]

        return (page,user,int(follows))
    else :
        return (page,user,0)

def post_crawler(users):
    thread_pool.Worker.timeout = None
    wm = thread_pool.WorkerManager(10)

    for user in users:
        wm.add_job(get_follower, user, 1)

    while True:
        try:
            return_item = wm.get_result(True, timeout = 90)
            current_page = return_item[0]
            current_user = return_item[1]
            follows      = return_item[2]
            print "user:%d page:%d finished" % (current_user,current_page)
            if follows > 20:
                pages = (int(follows)+20-1)/20
                for page in range(2,pages+1):
                    wm.add_job(get_follower, current_user, page)
        except Queue.Empty:
            break

def login(username,pwd,cookie_file):
    if os.path.exists(cookie_file):
        try:
            cookie_jar  = cookielib.LWPCookieJar(cookie_file)
            cookie_load = cookie_jar.load(ignore_discard=True, ignore_expires=True)
            loaded = 1
        except cookielib.LoadError:
            loaded = 0
            print 'error loading cookies'

        if loaded:
            cookie_support = urllib2.HTTPCookieProcessor(cookie_jar)
            opener         = urllib2.build_opener(cookie_support, urllib2.HTTPHandler)
            urllib2.install_opener(opener)
            return 1
        else:
            return do_login(username,pwd,cookie_file)
    else:
        return do_login(username,pwd,cookie_file)

def do_login(username,pwd,cookie_file):
    cookie_jar2     = cookielib.LWPCookieJar()
    cookie_support2 = urllib2.HTTPCookieProcessor(cookie_jar2)
    opener2         = urllib2.build_opener(cookie_support2, urllib2.HTTPHandler)
    urllib2.install_opener(opener2)
    login_url = 'http://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.3.18)'
    try:
        servertime, nonce = get_servertime()
    except:
        return
    global login_data
    login_data['servertime'] = servertime
    login_data['nonce'] = nonce
    login_data['su'] = get_user(username)
    login_data['sp'] = get_pwd(pwd, servertime, nonce)
    login_data = urllib.urlencode(login_data)
    http_headers = {'User-Agent':'Mozilla/5.0 (X11; Linux i686; rv:8.0) Gecko/20100101 Firefox/8.0'}
    req_login  = urllib2.Request(
        url = login_url,
        data = login_data,
        headers = http_headers
    )
    result = urllib2.urlopen(req_login)
    text = result.read()
    p = re.compile('location\.replace\(\'(.*?)\'\)')
    try:
        login_url = p.search(text).group(1)
        urllib2.urlopen(login_url)
        print "Login success!"
        cookie_jar2.save(cookie_file,ignore_discard=True, ignore_expires=True)
        return 1
    except:
        print 'Login error!'
        return 0

def main():
    username     = "18717746277"
    pwd          = "2&huffman"
    cookie_file  = "cookie_file.dat"

    login_status = login(username,pwd,cookie_file)

    if login_status:
        begin_url = "http://weibo.com/aj/mblog/mbloglist?_wv=5&page=1"
        d = urllib2.urlopen(begin_url).read()
        n = json.loads(d)
        m = n['data'].replace("\\", "")
        s = json.dumps(m,ensure_ascii=False).replace("</div>\\n\\t", "$")
        posts = re.findall(r"(<div[^>]*WB_text[^>]*feed_list_content[^>]*>)([^$]*)", s)
        for post in posts:
            print re.sub("<[^>]*>", "", post[1])


if __name__  ==  '__main__':
    main()
